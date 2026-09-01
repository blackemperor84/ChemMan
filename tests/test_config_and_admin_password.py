"""
Testy konfiguracji środowiskowej (WSGI/produkcja) oraz obsługi hasła administratora.

Pokrywa dwa problemy zgłoszone w audycie:
  - fabryka aplikacji ładowała bazowy Config, więc uruchomienie przez gunicorna
    nie aktywowało zabezpieczeń ProductionConfig (m.in. SESSION_COOKIE_SECURE),
  - skrypty administracyjne miały wbudowane hasła awaryjne ('F23pADFE!', 'admin').
"""
import os
from unittest import mock

import pytest

from app import resolve_config
from config import DevelopmentConfig, ProductionConfig, TestingConfig
from utils.admin_password import (
    ENV_VAR,
    MIN_PASSWORD_LENGTH,
    PasswordError,
    resolve_admin_password,
)


class TestResolveConfig:
    """FLASK_ENV musi decydować o wyborze klasy konfiguracji."""

    def test_production_env_selects_production_config(self, monkeypatch):
        monkeypatch.setenv('FLASK_ENV', 'production')
        assert resolve_config() is ProductionConfig

    def test_development_env_selects_development_config(self, monkeypatch):
        monkeypatch.setenv('FLASK_ENV', 'development')
        assert resolve_config() is DevelopmentConfig

    def test_testing_env_selects_testing_config(self, monkeypatch):
        monkeypatch.setenv('FLASK_ENV', 'testing')
        assert resolve_config() is TestingConfig

    def test_unset_env_defaults_to_development(self, monkeypatch):
        monkeypatch.delenv('FLASK_ENV', raising=False)
        assert resolve_config() is DevelopmentConfig

    def test_unknown_env_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv('FLASK_ENV', 'staging')
        assert resolve_config() is DevelopmentConfig

    def test_production_config_hardens_cookies(self):
        """Regresja: to są ustawienia, które gubiły się przy starcie przez WSGI."""
        assert ProductionConfig.SESSION_COOKIE_SECURE is True
        assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True
        assert ProductionConfig.REMEMBER_COOKIE_SECURE is True
        assert ProductionConfig.REMEMBER_COOKIE_HTTPONLY is True

    def test_development_config_does_not_require_https(self):
        """Development nie może wymuszać HTTPS - inaczej logowanie lokalnie nie działa."""
        assert getattr(DevelopmentConfig, 'SESSION_COOKIE_SECURE', False) is False


class TestResolveAdminPassword:
    """Brak jawnie podanego hasła musi być błędem, nie hasłem awaryjnym."""

    def test_reads_password_from_env(self):
        result = resolve_admin_password(
            getenv=lambda key: 'Str0ngPass!2026' if key == ENV_VAR else None,
            is_interactive=lambda: False,
        )
        assert result == 'Str0ngPass!2026'

    def test_refuses_when_unset_and_no_tty(self):
        """Najważniejszy przypadek: CI/systemd bez terminala."""
        with pytest.raises(PasswordError, match=ENV_VAR):
            resolve_admin_password(
                getenv=lambda key: None,
                is_interactive=lambda: False,
            )

    def test_refuses_when_env_var_is_empty_string(self):
        with pytest.raises(PasswordError, match=ENV_VAR):
            resolve_admin_password(
                getenv=lambda key: '',
                is_interactive=lambda: False,
            )

    def test_refuses_short_password_from_env(self):
        with pytest.raises(PasswordError, match='za krótkie'):
            resolve_admin_password(
                getenv=lambda key: 'short',
                is_interactive=lambda: False,
            )

    def test_accepts_password_at_minimum_length(self):
        password = 'a' * MIN_PASSWORD_LENGTH
        result = resolve_admin_password(
            getenv=lambda key: password,
            is_interactive=lambda: False,
        )
        assert result == password

    def test_prompts_interactively_when_env_unset(self):
        result = resolve_admin_password(
            getenv=lambda key: None,
            is_interactive=lambda: True,
            ask=lambda prompt: 'Interactive!123',
        )
        assert result == 'Interactive!123'

    def test_refuses_when_confirmation_does_not_match(self):
        answers = iter(['Interactive!123', 'Different!456'])

        with pytest.raises(PasswordError, match='identyczne'):
            resolve_admin_password(
                getenv=lambda key: None,
                is_interactive=lambda: True,
                ask=lambda prompt: next(answers),
            )

    def test_refuses_short_interactive_password(self):
        with pytest.raises(PasswordError, match='za krótkie'):
            resolve_admin_password(
                getenv=lambda key: None,
                is_interactive=lambda: True,
                ask=lambda prompt: 'abc',
            )

    def test_no_hardcoded_fallback_passwords_remain(self):
        """Regresja: stare hasła awaryjne nie mogą wrócić do skryptów."""
        import io
        import pathlib

        project_root = pathlib.Path(__file__).resolve().parent.parent
        for script in ('create_admin.py', 'update_admin_password.py', 'commands.py'):
            source = io.open(project_root / script, encoding='utf-8').read()
            assert 'F23pADFE' not in source, f"{script} zawiera stare hasło awaryjne"
            assert 'DEFAULT_PASSWORD' not in source, f"{script} używa starej nazwy zmiennej"
            # getenv z drugim argumentem = ciche hasło domyślne
            assert ".getenv('CHEM_MAN_ADMIN_PASSWORD'," not in source
            assert '.environ.get(\'CHEM_MAN_ADMIN_PASSWORD\',' not in source
            # config.get z drugim argumentem = to samo, tylko przez konfigurację
            assert "config.get('DEFAULT_ADMIN_PASSWORD'," not in source, (
                f"{script} ma ciche hasło awaryjne w config.get()"
            )

    def test_config_import_does_not_require_admin_password_in_production(self):
        """
        Obraz produkcyjny ma FLASK_ENV=production wpisane w Dockerfile. Import
        konfiguracji NIE może się wtedy wywalać z powodu braku
        CHEM_MAN_ADMIN_PASSWORD - inaczej aplikacji nie da się zrestartować po
        usunięciu tej zmiennej z .env, co dokumentacja wprost zaleca.
        """
        import importlib
        import io
        import pathlib

        project_root = pathlib.Path(__file__).resolve().parent.parent
        source = io.open(project_root / 'config.py', encoding='utf-8').read()
        assert 'raise ValueError' not in source.split('DEFAULT_ADMIN_PASSWORD')[1][:600], (
            "config.py znowu przerywa import przy braku CHEM_MAN_ADMIN_PASSWORD"
        )

        env = {'FLASK_ENV': 'production', 'SECRET_KEY': 'x' * 32}
        with mock.patch.dict(os.environ, env, clear=True):
            config_module = importlib.reload(importlib.import_module('config'))
            assert config_module.Config.DEFAULT_ADMIN_PASSWORD is None

        # przywróć moduł do stanu zgodnego z resztą sesji testowej
        importlib.reload(importlib.import_module('config'))

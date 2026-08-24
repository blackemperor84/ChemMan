"""
Testy łańcucha migracji Alembic.

Pokrywa problem zgłoszony w audycie: `flask db upgrade` na pustej bazie kończył się
błędem "no such table: substances", bo żadna migracja nie tworzyła podstawowych tabel.

Test integracyjny uruchamia prawdziwe `flask db upgrade` w podprocesie (env.py
Flask-Migrate wymaga kontekstu aplikacji, więc nie da się tego sensownie wywołać
w procesie testowym) i porównuje powstały schemat z tym, co generują modele.
"""
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSIONS_DIR = PROJECT_ROOT / 'migrations' / 'versions'
BASELINE_REVISION = 'chemman_baseline'


def _parse_revisions():
    """
    Czyta identyfikatory rewizji z plików migracji.

    Returns:
        dict: {revision: down_revision} (down_revision może być None)
    """
    revisions = {}
    for path in VERSIONS_DIR.glob('*.py'):
        source = path.read_text(encoding='utf-8')
        rev = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", source, re.M)
        down = re.search(r"^down_revision\s*=\s*(?:['\"]([^'\"]+)['\"]|None)", source, re.M)
        assert rev, f"{path.name}: brak identyfikatora revision"
        assert down, f"{path.name}: brak down_revision"
        revisions[rev.group(1)] = down.group(1)  # None gdy dopasowano gałąź 'None'
    return revisions


def _sqlite_schema(path):
    """
    Zwraca {tabela: {kolumna: (TYP, NOT NULL)}} dla bazy SQLite.
    """
    con = sqlite3.connect(path)
    try:
        tables = [
            row[0] for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version' ORDER BY name"
            ).fetchall()
        ]
        # Osobne fetchall() dla każdej tabeli - użycie jednego kursora
        # dla pętli zewnętrznej i PRAGMA ucina listę tabel.
        return {
            table: {
                row[1]: (row[2].upper(), bool(row[3]))
                for row in con.execute(f"PRAGMA table_info('{table}')").fetchall()
            }
            for table in tables
        }
    finally:
        con.close()


class TestMigrationChain:
    """Statyczna spójność łańcucha rewizji."""

    def test_exactly_one_root(self):
        """Dokładnie jedna migracja może być korzeniem i musi nią być baseline."""
        revisions = _parse_revisions()
        roots = [rev for rev, down in revisions.items() if down is None]
        assert roots == [BASELINE_REVISION], f"Oczekiwano jednego korzenia '{BASELINE_REVISION}', znaleziono: {roots}"

    def test_exactly_one_head(self):
        """Rozgałęziony łańcuch (kilka głów) zablokowałby `flask db upgrade`."""
        revisions = _parse_revisions()
        referenced = {down for down in revisions.values() if down is not None}
        heads = sorted(set(revisions) - referenced)
        assert len(heads) == 1, f"Oczekiwano jednej głowy, znaleziono: {heads}"

    def test_every_down_revision_exists(self):
        """Każdy down_revision musi wskazywać na istniejącą rewizję."""
        revisions = _parse_revisions()
        for rev, down in revisions.items():
            if down is not None:
                assert down in revisions, f"Rewizja '{rev}' wskazuje na nieistniejącą '{down}'"

    def test_chain_has_no_cycle(self):
        """Przejście od głowy do korzenia musi objąć wszystkie rewizje."""
        revisions = _parse_revisions()
        referenced = {d for d in revisions.values() if d is not None}
        head = (set(revisions) - referenced).pop()

        seen, current = [], head
        while current is not None:
            assert current not in seen, f"Cykl w łańcuchu migracji przy '{current}'"
            seen.append(current)
            current = revisions[current]

        assert len(seen) == len(revisions), (
            f"Łańcuch obejmuje {len(seen)} z {len(revisions)} rewizji - "
            f"osierocone: {sorted(set(revisions) - set(seen))}"
        )

    def test_baseline_creates_core_tables(self):
        """Baseline musi tworzyć tabele, których brak wywoływał 'no such table'."""
        source = None
        for path in VERSIONS_DIR.glob('*.py'):
            text = path.read_text(encoding='utf-8')
            # Dopasowanie zakotwiczone na początku linii - samo `in` złapałoby
            # też `down_revision = 'chemman_baseline'` w innym pliku.
            if re.search(rf"^revision\s*=\s*['\"]{BASELINE_REVISION}['\"]", text, re.M):
                source = text
                break
        assert source is not None, "Nie znaleziono pliku migracji baseline"

        for table in ('locations', 'users', 'substances', 'sds_files', 'audit_log'):
            assert f"'{table}'" in source, f"Baseline nie tworzy tabeli '{table}'"


class TestBooleanLiteralPortability:
    """Literały boolowskie muszą być renderowane per-dialekt, nie wpisane na sztywno."""

    @pytest.mark.parametrize('filename', [
        '779a32f7cb24_add_contains_cmr_and_contains_svhc_.py',
        'add_can_update_databases_permission.py',
    ])
    def test_no_raw_boolean_literals_in_sql_strings(self, filename):
        """
        Regresja: 'SET kolumna = 0' działa na SQLite, ale PostgreSQL odrzuca
        liczbę dla kolumny boolean.
        """
        source = (VERSIONS_DIR / filename).read_text(encoding='utf-8')
        raw_updates = re.findall(r"op\.execute\(\s*['\"]UPDATE[^'\"]*['\"]", source, re.I)
        assert not raw_updates, f"{filename}: surowy SQL UPDATE z literałem boolowskim: {raw_updates}"


class TestUpgradeFromEmptyDatabase:
    """
    Test integracyjny: pełny `flask db upgrade` na pustej bazie.

    Wolniejszy od reszty (uruchamia podproces), ale to jedyny sposób, by naprawdę
    sprawdzić, że świeża instalacja da się postawić z samych migracji.
    """

    @staticmethod
    def _run_flask_db_upgrade(db_path):
        env = dict(os.environ)
        env['DATABASE_URL'] = f'sqlite:///{db_path}'
        env['SECRET_KEY'] = 'migration-smoke-test-key'
        env['CHEM_MAN_ADMIN_PASSWORD'] = 'migration-smoke-test-pass'
        env['FLASK_ENV'] = 'development'
        env.pop('SQLALCHEMY_ECHO', None)

        return subprocess.run(
            [sys.executable, '-m', 'flask', 'db', 'upgrade'],
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

    def test_upgrade_succeeds_and_matches_model_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrated_db = os.path.join(tmpdir, 'migrated.db')

            result = self._run_flask_db_upgrade(migrated_db)
            assert result.returncode == 0, (
                f"'flask db upgrade' na pustej bazie zakończyło się błędem:\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
            assert os.path.exists(migrated_db), "Migracje nie utworzyły pliku bazy danych"

            migrated = _sqlite_schema(migrated_db)

            # Schemat wzorcowy prosto z modeli
            from models import db
            from app import create_app
            from config import TestingConfig

            reference_db = os.path.join(tmpdir, 'reference.db')

            class _RefConfig(TestingConfig):
                SQLALCHEMY_DATABASE_URI = f'sqlite:///{reference_db}'
                SQLALCHEMY_ECHO = False

            ref_app = create_app(_RefConfig)
            with ref_app.app_context():
                db.create_all()
                # Zwolnij uchwyt do pliku - na Windows otwarty engine
                # uniemożliwia sprzątnięcie katalogu tymczasowego.
                db.engine.dispose()
            reference = _sqlite_schema(reference_db)

            assert set(migrated) == set(reference), (
                f"Różnica w tabelach.\n"
                f"Brakuje w migracjach: {sorted(set(reference) - set(migrated))}\n"
                f"Nadmiarowe w migracjach: {sorted(set(migrated) - set(reference))}"
            )

            for table in sorted(reference):
                assert migrated[table] == reference[table], (
                    f"Tabela '{table}' różni się od modelu.\n"
                    f"  z migracji: {sorted(migrated[table].items())}\n"
                    f"  z modeli  : {sorted(reference[table].items())}"
                )

    def test_upgrade_creates_substances_table(self):
        """Konkretny objaw z audytu: 'no such table: substances'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            migrated_db = os.path.join(tmpdir, 'migrated.db')
            result = self._run_flask_db_upgrade(migrated_db)

            assert 'no such table' not in (result.stdout + result.stderr).lower()
            assert 'substances' in _sqlite_schema(migrated_db)

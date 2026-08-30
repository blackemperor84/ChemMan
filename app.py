import os
from datetime import datetime, timezone
from flask import Flask
from flask_login import LoginManager

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from config import Config, config as config_by_name
from models import db, bcrypt, User
from routes import register_blueprints

from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

import click
from flask.cli import with_appcontext

from limiter import limiter


def resolve_config():
    """
    Wybiera klasę konfiguracji na podstawie zmiennej środowiskowej FLASK_ENV.

    Returns:
        type: Klasa konfiguracji (DevelopmentConfig / TestingConfig / ProductionConfig)
    """
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, config_by_name['default'])


def create_app(config_class=None):
    """
    Fabryka aplikacji Flask.

    Args:
        config_class: Klasa konfiguracji. Gdy None (domyślnie), konfiguracja jest
                      wybierana na podstawie FLASK_ENV. Dzięki temu uruchomienie
                      przez WSGI (gunicorn) nie ląduje na bazowym `Config`, w którym
                      SESSION_COOKIE_SECURE i pozostałe zabezpieczenia produkcyjne
                      są wyłączone.
    """
    if config_class is None:
        config_class = resolve_config()

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Za odwrotnym proxy (nginx) kazde zadanie przychodzi z adresu proxy, wiec bez
    # ProxyFix wszyscy uzytkownicy dziela jeden limit. Wlaczane jawnie liczba
    # zaufanych proxy — bez tego naglowek X-Forwarded-For mozna podrobic.
    trusted_proxies = int(os.environ.get('TRUSTED_PROXY_COUNT', '0'))
    if trusted_proxies > 0:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=trusted_proxies, x_proto=trusted_proxies,
            x_host=trusted_proxies, x_port=trusted_proxies
        )

    # init_app po wczytaniu konfiguracji — flask-limiter czyta RATELIMIT_* wlasnie tutaj.
    limiter.init_app(app)
    csrf = CSRFProtect(app)  # Inicjalizacja CSRF
    
    # Inicjalizacja rozszerzeń z aplikacją
    db.init_app(app)
    bcrypt.init_app(app)
    migrate = Migrate(app, db)  # Inicjalizacja migracji bazy danych

    # Konfiguracja logowania
    # NOTE: Logging is now configured in config.py (DevelopmentConfig/ProductionConfig)
    # using RotatingFileHandler with automatic log rotation
    # configure_logging(app)  # Disabled - using config.py logging instead
    
    # Inicjalizacja Login Managera
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = app.config['LOGIN_VIEW']
    login_manager.login_message = app.config['LOGIN_MESSAGE']
    login_manager.login_message_category = app.config['LOGIN_MESSAGE_CATEGORY']
    
    from utils import convert_utc_to_local, nl2br
    app.jinja_env.globals.update(
        now=lambda: datetime.now(timezone.utc),
        convert_utc_to_local=convert_utc_to_local
    )
    app.jinja_env.filters['nl2br'] = nl2br
    
    # Konfiguracja dodatkowa aplikacji
    config_class.init_app(app)
    
    # Rejestracja blueprintów (modułów z trasami)
    register_blueprints(app)
    
    # Funkcja ładująca użytkownika dla Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Komenda CLI do inicjalizacji bazy danych
    @app.cli.command("init-db")
    def init_db_command():
        """Tworzy nowe tabele bazy danych (usuwając stare tabele)."""
        from commands import init_db_command as cmd_init_db
        cmd_init_db()

    @app.cli.command("import-excel")
    @with_appcontext
    def import_excel_command():
        """Importuje dane CLP z pliku Excel do tabeli excel_source_substances."""
        from flask import current_app
        from utils.database_import import import_clp_data
        excel_path = current_app.config.get('EXCEL_FILE_PATH')
        if not excel_path or not os.path.exists(excel_path):
            click.echo(f"Błąd: Plik Excel nie istnieje pod ścieżką: {excel_path}")
            return

        click.echo(f"Rozpoczynanie importu z: {excel_path}...")
        with open(excel_path, 'rb') as f:
            success, message, count = import_clp_data(f)
        click.echo(message)

    @app.cli.command("import-svhc")
    @with_appcontext
    def import_svhc_command():
        """Importuje dane SVHC z pliku Excel do tabeli svhc_substances."""
        from flask import current_app
        from utils.database_import import import_svhc_data
        svhc_path = current_app.config.get('SVHC_FILE_PATH')
        if not svhc_path or not os.path.exists(svhc_path):
            click.echo(f"Błąd: Plik SVHC Excel nie istnieje pod ścieżką: {svhc_path}")
            return

        click.echo(f"Rozpoczynanie importu SVHC z: {svhc_path}...")
        with open(svhc_path, 'rb') as f:
            success, message, count = import_svhc_data(f)
        click.echo(message)

    @app.cli.command("add-svhc-column")
    @with_appcontext
    def add_svhc_column_cmd():
        """Dodaje kolumnę is_svhc do tabeli substances."""
        from commands import add_svhc_column_command as cmd_add_svhc
        cmd_add_svhc()

    return app


if __name__ == '__main__':
    # Konfiguracja wybierana na podstawie FLASK_ENV (patrz resolve_config)
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app()
    app.logger.info(f"Uruchamianie aplikacji Chem-Man (env={env}, debug={app.debug})")
    app.run(debug=app.debug, host='0.0.0.0')
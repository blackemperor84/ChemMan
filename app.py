import os
import logging
import datetime
from flask import Flask
from flask_login import LoginManager

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from config import Config
from models import db, bcrypt, User, ExcelSourceSubstance, SVHCSubstance
from routes import register_blueprints

from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

import traceback
import click
import pandas as pd
from flask.cli import with_appcontext
from flask import current_app

from limiter import limiter


def create_app(config_class=Config):
    """Fabryka aplikacji Flask"""
    app = Flask(__name__)
    limiter.init_app(app)
    app.config.from_object(config_class)
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
    
    from utils import convert_utc_to_local
    app.jinja_env.globals.update(
        now=datetime.datetime.utcnow,
        convert_utc_to_local=convert_utc_to_local
    )
    
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
        """Importuje dane z pliku Excel do tabeli excel_source_substances."""
        excel_path = current_app.config.get('EXCEL_FILE_PATH')
        if not excel_path or not os.path.exists(excel_path):
            click.echo(f"Błąd: Plik Excel nie istnieje pod ścieżką: {excel_path}")
            return

        click.echo(f"Rozpoczynanie importu z: {excel_path}...")
        try:
            df = pd.read_excel(excel_path, header=0, skiprows=[1])
            click.echo(f"Wczytano {len(df)} wierszy z Excela.")

            # Mapowanie nazw kolumn z Excela na nazwy w modelu ExcelSourceSubstance
            column_map = {
                'International Chemical Identification': 'name',
                'CAS No': 'cas',
                'EC No': 'ec_number',
                'Classification': 'classification',
                'Unnamed: 5': 'h_phrases', # Zakładamy, że to kolumna F
                'Specific Conc. Limits, M-factors': 'scl_mfactor'
            }

            # Usuń kolumny z DataFrame, których nie ma w mapowaniu
            df.rename(columns=column_map, inplace=True)
            df = df[list(column_map.values())] # Zachowaj tylko zmapowane kolumny

            # Wyczyść starą tabelę przed importem
            click.echo("Czyszczenie tabeli excel_source_substances...")
            db.session.query(ExcelSourceSubstance).delete()
            db.session.commit() # Commit czyszczenia

            click.echo("Importowanie danych do bazy...")
            # Konwertuj DataFrame na listę słowników i dodaj do bazy
            data_to_insert = df.to_dict(orient='records')
            # Batch insert dla lepszej wydajności
            db.session.bulk_insert_mappings(ExcelSourceSubstance, data_to_insert)
            db.session.commit() # Commit importu

            click.echo(f"Import zakończony sukcesem. Dodano {len(data_to_insert)} rekordów.")

        except Exception as e:
            db.session.rollback()
            click.echo(f"Błąd podczas importu: {e}")
            traceback.print_exc()

    @app.cli.command("import-svhc")
    @with_appcontext
    def import_svhc_command():
        """Importuje dane z pliku SVHC Excel do tabeli svhc_substances."""
        svhc_path = current_app.config.get('SVHC_FILE_PATH')
        if not svhc_path or not os.path.exists(svhc_path):
            click.echo(f"Błąd: Plik SVHC Excel nie istnieje pod ścieżką: {svhc_path}")
            return

        click.echo(f"Rozpoczynanie importu SVHC z: {svhc_path}...")
        try:
            # Wczytaj plik Excel
            df = pd.read_excel(svhc_path, header=0)
            click.echo(f"Wczytano {len(df)} wierszy z SVHC Excela.")

            # Wyświetl wszystkie kolumny (dla debugowania)
            click.echo(f"Kolumny w pliku SVHC: {df.columns.tolist()}")

            # Próba mapowania kolumn - dostosuj do rzeczywistego układu pliku SVHC
            # Poniższe nazwy kolumn są przykładowe i mogą wymagać dostosowania
            column_map = {
                'Nazwa substancji ': 'name',
                'Nr WE': 'ec_number',
                'Nr CAS': 'cas',
                'Powód włączenia ': 'reason',
                'Data włączenia ': 'date_inclusion'
            }

            # Sprawdź, czy wszystkie kolumny istnieją
            missing_columns = [col for col in column_map.keys() if col not in df.columns]
            if missing_columns:
                click.echo(f"Ostrzeżenie: Brak następujących kolumn w pliku SVHC: {missing_columns}")
                # Dostosuj mapowanie tylko do istniejących kolumn
                column_map = {k: v for k, v in column_map.items() if k in df.columns}
                
            # Dopasuj nazwy kolumn w pliku SVHC
            if not column_map:
                # Automatyczne mapowanie na podstawie kluczowych słów w nazwach kolumn
                for col in df.columns:
                    col_lower = col.lower()
                    if 'name' in col_lower or 'substance' in col_lower:
                        column_map[col] = 'name'
                    elif 'cas' in col_lower:
                        column_map[col] = 'cas'
                    elif 'ec' in col_lower or 'number' in col_lower:
                        column_map[col] = 'ec_number'
                    elif 'reason' in col_lower or 'inclusion' in col_lower:
                        column_map[col] = 'reason'
                    elif 'date' in col_lower:
                        column_map[col] = 'date_inclusion'

            # Sprawdź, czy udało się zmapować podstawowe kolumny
            if 'name' not in column_map.values() and 'cas' not in column_map.values() and 'ec_number' not in column_map.values():
                click.echo("Błąd: Nie można zidentyfikować podstawowych kolumn w pliku SVHC.")
                return

            # Zmapuj kolumny i zachowaj tylko te, które są w modelu
            df.rename(columns=column_map, inplace=True)
            columns_to_keep = [v for v in column_map.values() if v in ['name', 'cas', 'ec_number', 'reason', 'date_inclusion']]
            
            # Dodaj brakujące kolumny jako puste
            for col in ['name', 'cas', 'ec_number', 'reason', 'date_inclusion']:
                if col not in columns_to_keep:
                    df[col] = None
                    columns_to_keep.append(col)
                    
            df = df[columns_to_keep]
            
            # Upewnij się, że wartości są stringami lub None
            for col in columns_to_keep:
                df[col] = df[col].astype(str).replace('nan', None)

            # Wyczyść starą tabelę przed importem
            click.echo("Czyszczenie tabeli svhc_substances...")
            db.session.query(SVHCSubstance).delete()
            db.session.commit()

            click.echo("Importowanie danych SVHC do bazy...")
            # Konwertuj DataFrame na listę słowników i dodaj do bazy
            data_to_insert = df.to_dict(orient='records')
            
            # Batch insert dla lepszej wydajności
            db.session.bulk_insert_mappings(SVHCSubstance, data_to_insert)
            db.session.commit()

            click.echo(f"Import SVHC zakończony sukcesem. Dodano {len(data_to_insert)} rekordów.")

        except Exception as e:
            db.session.rollback()
            click.echo(f"Błąd podczas importu SVHC: {e}")
            traceback.print_exc()
    
    @app.cli.command("add-svhc-column")
    @with_appcontext
    def add_svhc_column_cmd():
        """Dodaje kolumnę is_svhc do tabeli substances."""
        from commands import add_svhc_column_command as cmd_add_svhc
        cmd_add_svhc()
    
    return app


def configure_logging(app):
    """Konfiguruje logowanie aplikacji."""
    if not app.debug:
        # W trybie produkcyjnym loguj do pliku
        handler = logging.FileHandler('chem_man.log')
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
    else:
        # W trybie debug loguj do konsoli
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.DEBUG)
    
    # Usuń tę instrukcję return - ta funkcja powinna tylko konfigurować logowanie
    # return app


if __name__ == '__main__':
    # Determine which config to use based on FLASK_ENV
    from config import config
    env = os.environ.get('FLASK_ENV', 'development')
    config_class = config.get(env, config['development'])

    app = create_app(config_class)
    app.logger.info(f"Uruchamianie aplikacji Chem-Man (env={env}, debug={app.debug})")
    app.run(debug=app.debug, host='0.0.0.0')
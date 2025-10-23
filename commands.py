import os
import click
from flask import current_app
from flask.cli import with_appcontext
from models import db, User, SVHCSubstance

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Tworzy nowe tabele bazy danych (usuwając stare tabele)."""
    try:
        current_app.logger.info("Usuwanie istniejących tabel...")
        db.drop_all()
        current_app.logger.info("Tworzenie wszystkich tabel na nowo...")
        db.create_all()
        current_app.logger.info("Tabele bazy danych zostały utworzone pomyślnie.")
        
        # Upewnij się, że folder na upload istnieje
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        current_app.logger.info(f"Folder uploadu '{current_app.config['UPLOAD_FOLDER']}' sprawdzony/utworzony.")
        
        # Tworzenie domyślnego konta administratora
        try:
            # Pobierz hasło administratora z konfiguracji (z .env)
            admin_password = current_app.config.get('DEFAULT_ADMIN_PASSWORD', 'admin')

            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    is_admin=True,
                    can_view=True,
                    can_add=True,
                    can_edit=True,
                    can_delete=True,
                    can_move=True,
                    can_copy=True,
                    can_upload_sds=True
                )
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()
                current_app.logger.info(f"Domyślne konto administratora zostało utworzone z hasłem z konfiguracji.")
            else:
                # Upewnij się, że admin ma wszystkie uprawnienia
                admin_user.is_admin = True
                admin_user.can_view = True
                admin_user.can_add = True
                admin_user.can_edit = True
                admin_user.can_delete = True
                admin_user.can_move = True
                admin_user.can_copy = True
                admin_user.can_upload_sds = True
                # Zaktualizuj hasło do tego z konfiguracji
                admin_user.set_password(admin_password)
                db.session.commit()
                current_app.logger.info(f"Uprawnienia i hasło konta administratora zaktualizowane z konfiguracji.")
        except Exception as admin_err:
            current_app.logger.error(f"Błąd podczas konfiguracji konta admin: {admin_err}")
        
    except Exception as e:
        current_app.logger.error(f"Błąd podczas inicjalizacji bazy danych lub folderu: {e}")
        import traceback
        traceback.print_exc()

@click.command('add-permission-columns')
@with_appcontext
def add_permission_columns_command():
    """Dodaje kolumny uprawnień do tabeli users bez utraty danych."""
    try:
        current_app.logger.info("Dodawanie kolumn uprawnień do tabeli users...")
        
        # Sprawdź, czy kolumny już istnieją
        with db.engine.connect() as conn:
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('users')]
            
            # Lista kolumn do dodania
            permission_columns = [
                ('can_view', 'BOOLEAN', True),
                ('can_add', 'BOOLEAN', False),
                ('can_edit', 'BOOLEAN', False),
                ('can_delete', 'BOOLEAN', False),
                ('can_move', 'BOOLEAN', False),
                ('can_copy', 'BOOLEAN', False),
                ('can_upload_sds', 'BOOLEAN', False),
                ('can_add_location', 'BOOLEAN', False),
                ('can_delete_location', 'BOOLEAN', False)
            ]
            
            # Dodaj brakujące kolumny
            for col_name, col_type, default_value in permission_columns:
                if col_name not in columns:
                    # SQLite nie obsługuje ALTER TABLE ADD COLUMN z DEFAULT
                    if db.engine.url.drivername == 'sqlite':
                        default_clause = f"DEFAULT {1 if default_value else 0}"
                    else:
                        default_clause = f"DEFAULT {default_value}"
                    
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type} {default_clause}"
                    conn.execute(sql)
                    current_app.logger.info(f"Dodano kolumnę {col_name}")
            
            # Ustaw odpowiednie uprawnienia dla istniejących adminów
            conn.execute("""
                UPDATE users 
                SET can_view = 1, can_add = 1, can_edit = 1, can_delete = 1,
                    can_move = 1, can_copy = 1, can_upload_sds = 1
                WHERE is_admin = 1
            """)
            
            current_app.logger.info("Zakończono dodawanie kolumn uprawnień.")
            
    except Exception as e:
        current_app.logger.error(f"Błąd podczas dodawania kolumn uprawnień: {e}")
        import traceback
        traceback.print_exc()

@click.command('migrate-permissions')
@with_appcontext
def migrate_permissions_command():
    """Migruje uprawnienia istniejących użytkowników."""
    try:
        current_app.logger.info("Rozpoczynam migrację uprawnień użytkowników...")
        users = User.query.all()
        
        migrated_count = 0
        for user in users:
            changed = False
            
            # Upewnij się, że wszystkie pola uprawnień są zdefiniowane
            fields = ['can_view', 'can_add', 'can_edit', 'can_delete', 
                     'can_move', 'can_copy', 'can_upload_sds']
            
            for field in fields:
                if getattr(user, field, None) is None:
                    # Domyślna wartość: admin ma wszystkie uprawnienia, inni mają view
                    default_value = True if user.is_admin else (field == 'can_view')
                    setattr(user, field, default_value)
                    changed = True
            
            # Upewnij się, że admin ma wszystkie uprawnienia
            if user.is_admin:
                for field in fields:
                    if not getattr(user, field, True):
                        setattr(user, field, True)
                        changed = True
            
            if changed:
                migrated_count += 1
        
        if migrated_count > 0:
            db.session.commit()
            current_app.logger.info(f"Migracja zakończona. Zaktualizowano {migrated_count} użytkowników.")
        else:
            current_app.logger.info("Migracja zakończona. Nie było potrzeby aktualizacji użytkowników.")
        
    except Exception as e:
        current_app.logger.error(f"Błąd podczas migracji uprawnień: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

@click.command('add-svhc-column')
@with_appcontext
def add_svhc_column_command():
    """Dodaje kolumnę is_svhc do tabeli substances bez utraty danych."""
    try:
        current_app.logger.info("Dodawanie kolumny is_svhc do tabeli substances...")
        
        # Sprawdź, czy kolumna już istnieje
        with db.engine.connect() as conn:
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('substances')]
            
            if 'is_svhc' not in columns:
                # SQLite nie obsługuje ALTER TABLE ADD COLUMN z DEFAULT
                if db.engine.url.drivername == 'sqlite':
                    default_clause = "DEFAULT 0"
                else:
                    default_clause = "DEFAULT FALSE"
                
                sql = f"ALTER TABLE substances ADD COLUMN is_svhc BOOLEAN {default_clause}"
                conn.execute(sql)
                current_app.logger.info("Dodano kolumnę is_svhc")
                
                # Aktualizuj wartości is_svhc dla istniejących substancji
                current_app.logger.info("Aktualizacja wartości is_svhc dla istniejących substancji...")
                from utils import is_svhc_substance
                from models import Substance
                
                # Pobierz wszystkie substancje
                substances = Substance.query.all()
                updated_count = 0
                
                for sub in substances:
                    # Sprawdź, czy substancja jest na liście SVHC
                    is_svhc = is_svhc_substance(cas=sub.cas, ec_number=sub.ec_number, name=sub.name)
                    if is_svhc:
                        sub.is_svhc = True
                        updated_count += 1
                
                # Zapisz zmiany
                db.session.commit()
                current_app.logger.info(f"Zaktualizowano {updated_count} substancji jako SVHC")
            else:
                current_app.logger.info("Kolumna is_svhc już istnieje")
                
    except Exception as e:
        current_app.logger.error(f"Błąd podczas dodawania kolumny is_svhc: {e}")
        import traceback
        traceback.print_exc()
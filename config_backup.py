import os
from datetime import datetime
from datetime import timezone

# Ścieżka bazowa projektu
basedir = os.path.abspath(os.path.dirname(__file__))

# Klasa bazowa konfiguracji
class Config:
    """Podstawowa konfiguracja aplikacji Flask."""
    
    # Klucz tajny - używa zmiennej środowiskowej lub generuje tymczasowy
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # W środowisku produkcyjnym to wygeneruje błąd
        # W środowisku developerskim wygeneruje tymczasowy klucz
        if os.environ.get('FLASK_ENV') == 'production':
            raise ValueError("Nie ustawiono zmiennej środowiskowej SECRET_KEY! Aplikacja nie może bezpiecznie działać.")
        else:
            import secrets
            SECRET_KEY = secrets.token_hex(32)
            print("UWAGA: Wygenerowano tymczasowy SECRET_KEY dla środowiska developerskiego.")
    
    # Konfiguracja bazy danych SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'chem_man.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Konfiguracja uploadu plików SDS
    UPLOAD_FOLDER = os.path.join(basedir, 'instance', 'uploads', 'sds')
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 megabajtów
    
    # Ścieżka do pliku Excel
    EXCEL_FILE_PATH = os.path.join(basedir, 'substancje_baza.xlsx')
    
    # Ścieżka do pliku SVHC Excel
    SVHC_FILE_PATH = os.path.join(basedir, 'svhc.xlsx')
    
    # Strefa czasowa dla aplikacji
    TIMEZONE = 'Europe/Warsaw'
    
    # Ustawienia dla Flask-Login
    LOGIN_VIEW = 'auth.login'
    LOGIN_MESSAGE = "Musisz się zalogować, aby uzyskać dostęp do tej strony."
    LOGIN_MESSAGE_CATEGORY = "warning"
    
    # Konfiguracja JSON
    JSON_AS_ASCII = False
    
    # Hasło domyślne dla administratora - Lepiej czytać z zmiennej środowiskowej
    DEFAULT_ADMIN_PASSWORD = os.environ.get('CHEM_MAN_ADMIN_PASSWORD', 'admin')
    
    # Liczba rekordów na stronie w widokach z paginacją
    ITEMS_PER_PAGE = 25
    
    # Poziom logowania
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def init_app(app):
        """Inicjalizacja aplikacji z konfiguracją."""
        # Tworzenie niezbędnych folderów
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Udostępnienie aktualnego czasu dla szablonów Jinja
        app.jinja_env.globals.update(now=lambda: datetime.now(timezone.utc))


# Konfiguracja dla środowiska developerskiego
class DevelopmentConfig(Config):
    """Konfiguracja dla środowiska developerskiego."""
    DEBUG = True
    
    # Można włączyć tryb debugowania SQLAlchemy
    SQLALCHEMY_ECHO = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Dodatkowa konfiguracja dla trybu debug
        app.logger.setLevel('DEBUG')


# Konfiguracja dla środowiska testowego
class TestingConfig(Config):
    """Konfiguracja dla środowiska testowego."""
    TESTING = True
    
    # Użyj bazy danych w pamięci dla testów
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Upewnij się, że hasło testowe jest bezpieczne
    DEFAULT_ADMIN_PASSWORD = 'test_admin'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


# Konfiguracja dla środowiska produkcyjnego
class ProductionConfig(Config):
    """Konfiguracja dla środowiska produkcyjnego."""
    
    # W produkcji użyj bardziej zaawansowanej bazy danych jeśli to możliwe
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'chem_man_prod.db')
    
    # Dodatkowe zabezpieczenia dla produkcji
    SESSION_COOKIE_SECURE = True  # Używaj tylko przez HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Nie pozwalaj na dostęp przez JavaScript
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Dodatkowa konfiguracja dla produkcji
        # Np. konfiguracja logowania do pliku
        import logging
        from logging.handlers import RotatingFileHandler
        
        log_folder = os.path.join(basedir, 'logs')
        os.makedirs(log_folder, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_folder, 'chem_man.log'),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
        ))
        file_handler.setLevel(getattr(logging, cls.LOG_LEVEL))
        
        app.logger.addHandler(file_handler)


# Słownik możliwych konfiguracji
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
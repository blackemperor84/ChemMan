# Demo Configuration for ChemMan
# This file is used for the standalone demo version

import os
import secrets
from datetime import timedelta

class DemoConfig:
    """Configuration for Demo/Standalone version"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    FLASK_ENV = 'demo'
    DEBUG = False

    # Database - SQLite for demo (embedded, no installation needed)
    # Use absolute path for demo
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'demo_chemman.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Session
    SESSION_COOKIE_NAME = 'chemman_demo_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'pdf'}

    # Rate limiting (disabled for demo to avoid issues)
    RATELIMIT_ENABLED = False

    # Login
    LOGIN_VIEW = 'auth.login'
    LOGIN_MESSAGE = "Please log in to access this page."
    LOGIN_MESSAGE_CATEGORY = "warning"

    # Excel files
    EXCEL_FILE_PATH = os.path.join(basedir, '..', 'substancje_baza.xlsx')
    SVHC_FILE_PATH = os.path.join(basedir, '..', 'svhc.xlsx')

    # Timezone
    TIMEZONE = 'Europe/Warsaw'

    # JSON
    JSON_AS_ASCII = False

    # Pagination
    ITEMS_PER_PAGE = 25

    # Demo-specific settings
    DEMO_MODE = True
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'Demo1234'

    # Logging
    LOG_FILE = os.path.join(basedir, 'demo_chemman.log')
    LOG_LEVEL = 'INFO'

    @staticmethod
    def init_app(app):
        """Initialize application with demo configuration"""
        # Create necessary folders
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Make current time available in Jinja templates
        from datetime import datetime, timezone
        app.jinja_env.globals.update(now=lambda: datetime.now(timezone.utc))

"""
Punkt wejścia WSGI dla serwerów produkcyjnych (gunicorn, uWSGI, mod_wsgi).

Użycie:
    gunicorn -c gunicorn_config.py wsgi:app

Konfiguracja jest wybierana na podstawie zmiennej środowiskowej FLASK_ENV.
W produkcji ustaw FLASK_ENV=production, aby aktywować ProductionConfig
(SESSION_COOKIE_SECURE, REMEMBER_COOKIE_SECURE, logowanie do pliku).

NIE używaj `app:create_app()` jako celu gunicorna - patrz historia: taki zapis
działał, ale w starszej wersji fabryki ładował bazowy `Config` bez zabezpieczeń
produkcyjnych.
"""
import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app, resolve_config

# create_app() bez argumentu wybiera konfigurację na podstawie FLASK_ENV
app = create_app()

if os.environ.get('FLASK_ENV') != 'production':
    app.logger.warning(
        f"WSGI: FLASK_ENV={os.environ.get('FLASK_ENV', 'development')} - "
        f"uruchomiono z {resolve_config().__name__}, NIE z ProductionConfig. "
        f"Ustaw FLASK_ENV=production przed wdrożeniem."
    )

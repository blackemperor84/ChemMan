"""
Zmienia hasło istniejącego użytkownika 'admin'.

Hasło NIE ma wartości domyślnej. Podaj je jedną z dwóch dróg:
  1. zmienna środowiskowa CHEM_MAN_ADMIN_PASSWORD (np. z pliku .env), albo
  2. interaktywnie - skrypt zapyta i nie wyświetli hasła na ekranie.

Skrypt kończy się błędem, jeśli hasła nie da się uzyskać (np. w CI bez TTY).
"""
import sys

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from models import db, User
from utils.admin_password import PasswordError, resolve_admin_password

app = create_app()

with app.app_context():
    admin_user = User.query.filter_by(username='admin').first()

    if not admin_user:
        sys.exit(
            "BŁĄD: Nie znaleziono użytkownika 'admin' w bazie danych.\n"
            "       Uruchom najpierw create_admin.py"
        )

    try:
        new_password = resolve_admin_password('Nowe hasło dla użytkownika admin: ')
    except PasswordError as exc:
        sys.exit(f"BŁĄD: {exc}")

    admin_user.set_password(new_password)
    db.session.commit()

    # Hasło NIE jest wypisywane - trafiłoby do historii powłoki i logów CI
    print("SUKCES: Zaktualizowano hasło użytkownika 'admin'.")

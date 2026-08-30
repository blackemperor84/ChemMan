"""
Tworzy użytkownika 'admin', jeśli jeszcze nie istnieje.

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
    admin = User.query.filter_by(username='admin').first()

    if admin:
        print("Użytkownik 'admin' już istnieje - nic nie zmieniono.")
        print("Aby zmienić hasło, użyj update_admin_password.py")
        sys.exit(0)

    try:
        admin_password = resolve_admin_password('Hasło dla nowego użytkownika admin: ')
    except PasswordError as exc:
        sys.exit(f"BŁĄD: {exc}")

    print("Tworzenie użytkownika 'admin'...")
    admin = User(
        username='admin',
        is_admin=True,
        can_view=True,
        can_add=True,
        can_edit=True,
        can_delete=True,
        can_move=True,
        can_copy=True,
        can_upload_sds=True,
        can_add_location=True,
        can_delete_location=True
    )
    admin.set_password(admin_password)

    db.session.add(admin)
    db.session.commit()

    # Hasło NIE jest wypisywane - trafiłoby do historii powłoki i logów CI
    print("SUKCES: Utworzono użytkownika 'admin'.")
    print("        Nazwa użytkownika: admin")
    print("        Hasło: to, które podano powyżej")

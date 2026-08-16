"""
Build Demo Database for ChemMan
Creates a pre-populated SQLite database for the demo version.

Uses the shared import helpers from utils.database_import so any bug fix
or format change to the CLP/SVHC parsing applies here automatically.
"""

import os
import sys

# Add parent directory to path to import from main app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set environment to ensure demo database is used
demo_db_path = os.path.join(os.path.dirname(__file__), 'demo_chemman.db')
os.environ['DATABASE_URL'] = f'sqlite:///{demo_db_path}'
os.environ['FLASK_ENV'] = 'demo'

from app import create_app
from models import db, User, ExcelSourceSubstance, SVHCSubstance
from utils.database_import import import_clp_data, import_svhc_data
from config_demo import DemoConfig


CLP_XLSX_CANDIDATES = ['substancje_baza.xlsx']
SVHC_XLSX_CANDIDATES = ['svhc.xlsx', 'svhc__current.xlsx']


def _find_source(candidates):
    """Return the first existing source file from the parent directory."""
    parent = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    for name in candidates:
        path = os.path.join(parent, name)
        if os.path.exists(path):
            return path
    return None


def create_demo_database():
    """Create and populate demo database."""
    print("ChemMan - Building Demo Database")
    print("=" * 50)

    app = create_app(DemoConfig)

    with app.app_context():
        print("\nStep 1: Creating database schema...")
        db.create_all()
        print("[OK] Schema created")

        print("\nStep 2: Creating admin user...")
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("[WARN] Admin already exists, deleting...")
            db.session.delete(admin)
            db.session.commit()

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
            can_delete_location=True,
            can_update_databases=True,
        )
        admin.set_password('Demo1234')
        db.session.add(admin)
        db.session.commit()
        print("[OK] Admin user created (username: admin, password: Demo1234)")

        print("\nStep 3: Importing CLP database...")
        clp_path = _find_source(CLP_XLSX_CANDIDATES)
        if not clp_path:
            print(f"[ERROR] CLP source file not found. Looked for: {CLP_XLSX_CANDIDATES}")
            return False
        print(f"       Source: {clp_path}")
        with open(clp_path, 'rb') as f:
            ok, message, count = import_clp_data(f)
        if not ok:
            print(f"[ERROR] {message}")
            return False
        print(f"[OK] {message}")

        print("\nStep 4: Importing SVHC database...")
        svhc_path = _find_source(SVHC_XLSX_CANDIDATES)
        if not svhc_path:
            print(f"[ERROR] SVHC source file not found. Looked for: {SVHC_XLSX_CANDIDATES}")
            return False
        print(f"       Source: {svhc_path}")
        with open(svhc_path, 'rb') as f:
            ok, message, count_svhc = import_svhc_data(f)
        if not ok:
            print(f"[ERROR] {message}")
            return False
        print(f"[OK] {message}")

        clp_count = ExcelSourceSubstance.query.count()
        svhc_count = SVHCSubstance.query.count()

        print("\n" + "=" * 50)
        print("[SUCCESS] Demo database built successfully!")
        print(f"CLP Substances: {clp_count}")
        print(f"SVHC Substances: {svhc_count}")
        print(f"Admin User: admin / Demo1234")
        print(f"Database: {DemoConfig.SQLALCHEMY_DATABASE_URI}")
        print("=" * 50)

        return True


if __name__ == '__main__':
    success = create_demo_database()
    sys.exit(0 if success else 1)

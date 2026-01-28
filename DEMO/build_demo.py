"""
Build Demo Database for ChemMan
Creates a pre-populated SQLite database for the demo version
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
from config_demo import DemoConfig
import pandas as pd

def create_demo_database():
    """Create and populate demo database"""

    print("ChemMan - Building Demo Database")
    print("=" * 50)

    # Create app with demo config
    app = create_app(DemoConfig)

    with app.app_context():
        # 1. Create all tables
        print("\nStep 1: Creating database schema...")
        db.create_all()
        print("[OK] Schema created")

        # 2. Create admin user
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
            can_update_databases=True
        )
        admin.set_password('Demo1234')
        db.session.add(admin)
        db.session.commit()
        print("[OK] Admin user created (username: admin, password: Demo1234)")

        # 3. Import CLP database
        print("\nStep 3: Importing CLP database...")
        excel_path = os.path.join(os.path.dirname(__file__), '..', 'substancje_baza.xlsx')

        if not os.path.exists(excel_path):
            print(f"[ERROR] File not found: {excel_path}")
            print("Please ensure substancje_baza.xlsx is in the parent directory")
            return False

        df = pd.read_excel(excel_path, header=0, skiprows=[1])

        column_map = {
            'International Chemical Identification': 'name',
            'CAS No': 'cas',
            'EC No': 'ec_number',
            'Classification': 'classification',
            'Unnamed: 5': 'h_phrases',
            'Specific Conc. Limits, M-factors': 'scl_mfactor'
        }

        df.rename(columns=column_map, inplace=True)
        df = df[list(column_map.values())]

        # Clear existing data
        db.session.query(ExcelSourceSubstance).delete()
        db.session.commit()

        # Import with type conversion
        def safe_str(val):
            if pd.isna(val):
                return None
            return str(val)

        count = 0
        for idx, row in df.iterrows():
            substance = ExcelSourceSubstance(
                name=safe_str(row['name']),
                cas=safe_str(row['cas']),
                ec_number=safe_str(row['ec_number']),
                classification=safe_str(row['classification']),
                h_phrases=safe_str(row['h_phrases']),
                scl_mfactor=safe_str(row['scl_mfactor'])
            )
            db.session.add(substance)
            count += 1

            if count % 100 == 0:
                db.session.commit()
                print(f"  Imported {count} substances...")

        # Commit remaining
        if count % 100 != 0:
            db.session.commit()

        print(f"[OK] Imported {count} CLP substances")

        # 4. Import SVHC database
        print("\nStep 4: Importing SVHC database...")
        svhc_path = os.path.join(os.path.dirname(__file__), '..', 'svhc.xlsx')

        if not os.path.exists(svhc_path):
            print(f"[ERROR] File not found: {svhc_path}")
            print("Please ensure svhc.xlsx is in the parent directory")
            return False

        df_svhc = pd.read_excel(svhc_path, header=0)

        column_map_svhc = {
            'Nazwa substancji ': 'name',
            'Nr WE': 'ec_number',
            'Nr CAS': 'cas',
            'Powód włączenia ': 'reason',
            'Data włączenia ': 'date_inclusion'
        }

        df_svhc.rename(columns=column_map_svhc, inplace=True)

        for col in ['name', 'cas', 'ec_number', 'reason', 'date_inclusion']:
            if col not in df_svhc.columns:
                df_svhc[col] = None

        df_svhc = df_svhc[['name', 'cas', 'ec_number', 'reason', 'date_inclusion']]

        # Clear existing data
        db.session.query(SVHCSubstance).delete()
        db.session.commit()

        count_svhc = 0
        for idx, row in df_svhc.iterrows():
            svhc = SVHCSubstance(
                name=safe_str(row['name']),
                cas=safe_str(row['cas']),
                ec_number=safe_str(row['ec_number']),
                reason=safe_str(row['reason']),
                date_inclusion=safe_str(row['date_inclusion'])
            )
            db.session.add(svhc)
            count_svhc += 1

            if count_svhc % 50 == 0:
                db.session.commit()
                print(f"  Imported {count_svhc} SVHC substances...")

        # Commit remaining
        if count_svhc % 50 != 0:
            db.session.commit()

        print(f"[OK] Imported {count_svhc} SVHC substances")

        # 5. Summary
        print("\n" + "=" * 50)
        print("[SUCCESS] Demo database built successfully!")
        print(f"CLP Substances: {count}")
        print(f"SVHC Substances: {count_svhc}")
        print(f"Admin User: admin / Demo1234")
        print(f"Database: {DemoConfig.SQLALCHEMY_DATABASE_URI}")
        print("=" * 50)

        return True

if __name__ == '__main__':
    success = create_demo_database()
    sys.exit(0 if success else 1)

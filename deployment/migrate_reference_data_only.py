"""
Simple migration: Only migrate ExcelSourceSubstances and SVHCSubstances
User data (users, locations, substances) should be re-created manually
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ExcelSourceSubstance, SVHCSubstance

sqlite_db = 'sqlite:///instance/chem_man.db'
postgres_db = 'postgresql://chemman_user:chemman_pass123@localhost:5432/chemman_dev'

print("=" * 60)
print("Migrating Reference Data (Excel & SVHC)")
print("=" * 60)

# Connect to databases
sqlite_engine = create_engine(sqlite_db)
postgres_engine = create_engine(postgres_db)

SqliteSession = sessionmaker(bind=sqlite_engine)
PostgresSession = sessionmaker(bind=postgres_engine)

sqlite_session = SqliteSession()
postgres_session = PostgresSession()

try:
    # Migrate ExcelSourceSubstances
    print("\n1. Migrating Excel Source Substances...")
    count = sqlite_session.query(ExcelSourceSubstance).count()
    print(f"   Found {count} records")

    for i, record in enumerate(sqlite_session.query(ExcelSourceSubstance).all(), 1):
        new_record = ExcelSourceSubstance(
            name=record.name,
            cas=record.cas,
            ec_number=record.ec_number,
            classification=record.classification,
            h_phrases=record.h_phrases,
            scl_mfactor=record.scl_mfactor
        )
        postgres_session.add(new_record)

        if i % 500 == 0:
            postgres_session.commit()
            print(f"   Progress: {i}/{count}")

    postgres_session.commit()
    print(f"   [OK] Migrated {count} Excel records")

    # Migrate SVHCSubstances
    print("\n2. Migrating SVHC Substances...")
    count = sqlite_session.query(SVHCSubstance).count()
    print(f"   Found {count} records")

    for record in sqlite_session.query(SVHCSubstance).all():
        new_record = SVHCSubstance(
            name=record.name,
            cas=record.cas,
            ec_number=record.ec_number,
            reason=record.reason,
            date_inclusion=record.date_inclusion
        )
        postgres_session.add(new_record)

    postgres_session.commit()
    print(f"   [OK] Migrated {count} SVHC records")

    print("\n" + "=" * 60)
    print("[SUCCESS] Reference data migrated!")
    print("=" * 60)
    print("\nNote: User data not migrated.")
    print("Please recreate users, locations, and substances manually.")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] {e}")
    postgres_session.rollback()
finally:
    sqlite_session.close()
    postgres_session.close()

"""
SQLite to PostgreSQL Migration Script for Chem-Man Application
This script migrates all data from SQLite to PostgreSQL.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import db, User, Location, Substance, ExcelSourceSubstance, SVHCSubstance, AuditLog
from app import create_app
from config import DevelopmentConfig

def migrate_data():
    """Migrate data from SQLite to PostgreSQL."""

    print("=" * 70)
    print("Chem-Man: SQLite to PostgreSQL Migration")
    print("=" * 70)

    # SQLite database path
    sqlite_db = 'sqlite:///instance/chem_man.db'

    # PostgreSQL database (from .env)
    postgres_db = 'postgresql://chemman_user:chemman_pass123@localhost:5432/chemman_dev'

    print(f"\nSource:      {sqlite_db}")
    print(f"Destination: {postgres_db}")
    print("=" * 70)

    try:
        # Connect to SQLite
        print("\n1. Connecting to SQLite database...")
        sqlite_engine = create_engine(sqlite_db)
        SqliteSession = sessionmaker(bind=sqlite_engine)
        sqlite_session = SqliteSession()
        print("   [OK] Connected to SQLite")

        # Connect to PostgreSQL
        print("\n2. Connecting to PostgreSQL database...")
        postgres_engine = create_engine(postgres_db)
        PostgresSession = sessionmaker(bind=postgres_engine)
        postgres_session = PostgresSession()
        print("   [OK] Connected to PostgreSQL")

        # Create tables in PostgreSQL
        print("\n3. Creating tables in PostgreSQL...")
        app = create_app(DevelopmentConfig)
        with app.app_context():
            # Temporarily override DATABASE_URL to use PostgreSQL
            app.config['SQLALCHEMY_DATABASE_URI'] = postgres_db
            db.create_all()
        print("   [OK] Tables created")

        # Define models to migrate (order matters for foreign keys!)
        models_to_migrate = [
            ('Users', User),
            ('Locations', Location),
            ('Substances', Substance),
            ('ExcelSourceSubstances', ExcelSourceSubstance),
            ('SVHCSubstances', SVHCSubstance),
            ('AuditLogs', AuditLog),
        ]

        total_records = 0

        # Migrate each model
        for model_name, model_class in models_to_migrate:
            print(f"\n4. Migrating {model_name}...")

            # Count records in SQLite
            count = sqlite_session.query(model_class).count()
            print(f"   Found {count} records in SQLite")

            if count == 0:
                print(f"   [SKIP] No {model_name} to migrate")
                continue

            # Fetch all records from SQLite
            records = sqlite_session.query(model_class).all()

            # Copy to PostgreSQL
            migrated = 0
            for record in records:
                # Create a dictionary of the record's attributes (excluding 'id' - let PostgreSQL generate it)
                record_dict = {}
                for column in model_class.__table__.columns:
                    # Skip 'id' column - let PostgreSQL auto-generate it
                    if column.name != 'id':
                        record_dict[column.name] = getattr(record, column.name)

                # Create new instance for PostgreSQL
                new_record = model_class(**record_dict)
                postgres_session.add(new_record)
                migrated += 1

                # Commit in batches of 100
                if migrated % 100 == 0:
                    postgres_session.commit()
                    print(f"   Progress: {migrated}/{count}")

            # Final commit
            postgres_session.commit()
            print(f"   [OK] Migrated {migrated} {model_name}")
            total_records += migrated

        # Close sessions
        sqlite_session.close()
        postgres_session.close()

        print("\n" + "=" * 70)
        print(f"[SUCCESS] Migration completed!")
        print(f"Total records migrated: {total_records}")
        print("=" * 70)

        # Verify migration
        print("\nVerifying migration...")
        PostgresSession2 = sessionmaker(bind=postgres_engine)
        verify_session = PostgresSession2()

        for model_name, model_class in models_to_migrate:
            count = verify_session.query(model_class).count()
            print(f"  {model_name}: {count} records")

        verify_session.close()

        print("\n" + "=" * 70)
        print("Migration verification complete!")
        print("=" * 70)

        print("\nNext steps:")
        print("  1. Test the application with PostgreSQL")
        print("  2. Run test suite: pytest tests/")
        print("  3. If all works, backup SQLite and continue with PostgreSQL")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        print("\nRolling back changes...")
        if 'postgres_session' in locals():
            postgres_session.rollback()
        return False

if __name__ == "__main__":
    success = migrate_data()
    sys.exit(0 if success else 1)

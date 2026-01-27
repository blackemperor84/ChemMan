"""
PostgreSQL Database Setup Script for Chem-Man Application
This script creates the database and user for the application.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

def setup_database():
    """Create PostgreSQL database and user for Chem-Man."""

    # Configuration
    POSTGRES_USER = 'postgres'
    POSTGRES_PASSWORD = 'admin!'  # Change this to your postgres password
    POSTGRES_HOST = 'localhost'
    POSTGRES_PORT = '5432'

    # Database and user to create
    DB_NAME = 'chemman_dev'
    DB_USER = 'chemman_user'
    DB_PASSWORD = 'chemman_pass123'

    print("=" * 60)
    print("Chem-Man PostgreSQL Database Setup")
    print("=" * 60)

    try:
        # Connect to PostgreSQL as superuser
        print(f"\n1. Connecting to PostgreSQL as '{POSTGRES_USER}'...")
        conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database='postgres'  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("   [OK] Connected successfully!")

        # Check if database already exists
        print(f"\n2. Checking if database '{DB_NAME}' exists...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()

        if exists:
            print(f"   [WARN] Database '{DB_NAME}' already exists. Skipping creation.")
        else:
            # Create database
            print(f"   Creating database '{DB_NAME}'...")
            cursor.execute(f'CREATE DATABASE {DB_NAME}')
            print(f"   [OK] Database '{DB_NAME}' created successfully!")

        # Check if user already exists
        print(f"\n3. Checking if user '{DB_USER}' exists...")
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (DB_USER,))
        user_exists = cursor.fetchone()

        if user_exists:
            print(f"   [WARN] User '{DB_USER}' already exists. Skipping creation.")
        else:
            # Create user
            print(f"   Creating user '{DB_USER}'...")
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
            print(f"   [OK] User '{DB_USER}' created successfully!")

        # Grant privileges
        print(f"\n4. Granting privileges to '{DB_USER}' on '{DB_NAME}'...")
        cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}')
        print(f"   [OK] Privileges granted!")

        # Close connection to postgres database
        cursor.close()
        conn.close()

        # Connect to the new database to set schema privileges
        print(f"\n5. Configuring schema privileges...")
        conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=DB_NAME
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Grant schema privileges (PostgreSQL 15+)
        cursor.execute(f'GRANT ALL ON SCHEMA public TO {DB_USER}')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER}')
        cursor.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER}')
        print(f"   [OK] Schema privileges configured!")

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("[SUCCESS] Database setup completed successfully!")
        print("=" * 60)
        print(f"\nDatabase Details:")
        print(f"  Database Name: {DB_NAME}")
        print(f"  Username:      {DB_USER}")
        print(f"  Password:      {DB_PASSWORD}")
        print(f"  Host:          {POSTGRES_HOST}")
        print(f"  Port:          {POSTGRES_PORT}")
        print(f"\nConnection String:")
        print(f"  postgresql://{DB_USER}:{DB_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DB_NAME}")
        print("=" * 60)

        return True

    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        print("\nPossible issues:")
        print("  - Check if PostgreSQL is running")
        print("  - Verify the postgres user password is correct")
        print("  - Ensure PostgreSQL is accepting connections on localhost:5432")
        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)

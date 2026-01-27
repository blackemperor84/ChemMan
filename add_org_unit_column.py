"""Script to add organizational_unit_id column to users table if it doesn't exist"""

from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check if column exists
    result = db.session.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'organizational_unit_id'
    """))

    column_exists = result.fetchone() is not None

    if column_exists:
        print("[OK] Column 'organizational_unit_id' already exists in 'users' table")
    else:
        print("Adding 'organizational_unit_id' column to 'users' table...")

        try:
            # Add the column
            db.session.execute(text("""
                ALTER TABLE users
                ADD COLUMN organizational_unit_id INTEGER
            """))

            # Add foreign key constraint
            db.session.execute(text("""
                ALTER TABLE users
                ADD CONSTRAINT fk_users_organizational_unit_id
                FOREIGN KEY (organizational_unit_id)
                REFERENCES locations(id)
            """))

            db.session.commit()
            print("[OK] Successfully added 'organizational_unit_id' column and foreign key constraint")
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] {e}")
            raise

print("\nDatabase update complete!")
print("\nNext steps:")
print("1. Go to /admin/users to assign users to organizational units")
print("2. Test access control by logging in as different users")

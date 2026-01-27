"""
Migration script to add:
1. Multiple SDS files support via new sds_files table
2. CMR/SVHC flags for mixtures (contains_cmr, contains_svhc) to substances table
"""

from app import create_app
from models import db, SDSFile
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 70)
    print("DATABASE MIGRATION: Multiple SDS Files & Mixture CMR/SVHC Flags")
    print("=" * 70)

    # Step 1: Add contains_cmr and contains_svhc columns to substances table
    print("\n[STEP 1] Adding CMR/SVHC flags for mixtures to substances table...")

    # Check if contains_cmr column exists
    result = db.session.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'substances'
        AND column_name = 'contains_cmr'
    """))

    if result.fetchone() is None:
        try:
            db.session.execute(text("""
                ALTER TABLE substances
                ADD COLUMN contains_cmr BOOLEAN DEFAULT FALSE
            """))
            db.session.commit()
            print("  [OK] Added 'contains_cmr' column")
        except Exception as e:
            db.session.rollback()
            print(f"  [ERROR] Failed to add 'contains_cmr': {e}")
    else:
        print("  [SKIP] Column 'contains_cmr' already exists")

    # Check if contains_svhc column exists
    result = db.session.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'substances'
        AND column_name = 'contains_svhc'
    """))

    if result.fetchone() is None:
        try:
            db.session.execute(text("""
                ALTER TABLE substances
                ADD COLUMN contains_svhc BOOLEAN DEFAULT FALSE
            """))
            db.session.commit()
            print("  [OK] Added 'contains_svhc' column")
        except Exception as e:
            db.session.rollback()
            print(f"  [ERROR] Failed to add 'contains_svhc': {e}")
    else:
        print("  [SKIP] Column 'contains_svhc' already exists")

    # Step 2: Create sds_files table
    print("\n[STEP 2] Creating sds_files table...")

    # Check if table exists
    result = db.session.execute(text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = 'sds_files'
    """))

    if result.fetchone() is None:
        try:
            db.session.execute(text("""
                CREATE TABLE sds_files (
                    id SERIAL PRIMARY KEY,
                    substance_id INTEGER NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255),
                    manufacturer VARCHAR(255),
                    upload_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_sds_files_substance_id
                        FOREIGN KEY (substance_id)
                        REFERENCES substances(id)
                        ON DELETE CASCADE
                )
            """))
            db.session.commit()
            print("  [OK] Created 'sds_files' table")
        except Exception as e:
            db.session.rollback()
            print(f"  [ERROR] Failed to create 'sds_files' table: {e}")
            raise
    else:
        print("  [SKIP] Table 'sds_files' already exists")

    # Step 3: Migrate existing SDS files to new table
    print("\n[STEP 3] Migrating existing SDS files to new table...")

    try:
        # Get all substances with existing SDS files
        result = db.session.execute(text("""
            SELECT id, sds_filename, sds_upload_timestamp
            FROM substances
            WHERE sds_filename IS NOT NULL AND sds_filename != ''
        """))

        substances_with_sds = result.fetchall()
        migrated_count = 0

        for sub_id, filename, timestamp in substances_with_sds:
            # Check if already migrated
            existing = db.session.execute(text("""
                SELECT id FROM sds_files
                WHERE substance_id = :sub_id AND filename = :filename
            """), {'sub_id': sub_id, 'filename': filename}).fetchone()

            if existing is None:
                # Insert into sds_files table
                db.session.execute(text("""
                    INSERT INTO sds_files (substance_id, filename, original_filename, upload_timestamp)
                    VALUES (:sub_id, :filename, :orig_filename, :timestamp)
                """), {
                    'sub_id': sub_id,
                    'filename': filename,
                    'orig_filename': filename,  # Use same filename as original
                    'timestamp': timestamp if timestamp else 'CURRENT_TIMESTAMP'
                })
                migrated_count += 1

        db.session.commit()
        print(f"  [OK] Migrated {migrated_count} existing SDS files to new table")

    except Exception as e:
        db.session.rollback()
        print(f"  [ERROR] Failed to migrate existing SDS files: {e}")
        raise

    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE!")
    print("=" * 70)
    print("\nChanges applied:")
    print("  1. Added 'contains_cmr' column to substances table")
    print("  2. Added 'contains_svhc' column to substances table")
    print("  3. Created 'sds_files' table for multiple SDS files per substance")
    print(f"  4. Migrated {migrated_count} existing SDS files to new table")
    print("\nNote: The old 'sds_filename' and 'sds_upload_timestamp' columns are kept")
    print("      for backward compatibility but will no longer be used by the app.")
    print("\n" + "=" * 70)

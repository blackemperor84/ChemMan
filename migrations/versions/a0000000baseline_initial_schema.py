"""Baseline: podstawowe tabele aplikacji (locations, users, substances, sds_files, audit_log)

Revision ID: chemman_baseline
Revises:
Create Date: 2026-08-24

Kontekst historyczny
--------------------
Te tabele powstawały pierwotnie przez `db.create_all()`, a nie przez migracje.
Łańcuch migracji zaczynał się od '0c94b152b44c', które tworzy jedynie
`excel_source_substances`, a już kolejna rewizja ('eba4b0241b18') próbowała
zmodyfikować tabelę `substances`. W efekcie `flask db upgrade` na pustej bazie
kończył się błędem:

    sqlite3.OperationalError: no such table: substances

Ta rewizja jest nowym korzeniem łańcucha i tworzy brakujące tabele w kształcie,
jaki miały PRZED późniejszymi migracjami. Kolumny dodawane później celowo NIE
występują tutaj - dokłada je odpowiednia rewizja:

  * substances.is_svhc                      -> eba4b0241b18
  * substances.contains_cmr/contains_svhc   -> 779a32f7cb24
  * users.organizational_unit_id            -> add_org_unit_2025
  * users.can_update_databases              -> add_update_db_perm

Istniejące bazy danych są już oznaczone (stamped) rewizją z dalszej części
łańcucha, więc ta migracja się na nich NIE wykona - dotyczy tylko instalacji
zakładanych od zera.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'chemman_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Kolejność ma znaczenie ze względu na klucze obce:
    # locations -> users -> substances -> sds_files -> audit_log

    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('last_modified', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=128), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('can_view', sa.Boolean(), nullable=True),
        sa.Column('can_add', sa.Boolean(), nullable=True),
        sa.Column('can_edit', sa.Boolean(), nullable=True),
        sa.Column('can_delete', sa.Boolean(), nullable=True),
        sa.Column('can_move', sa.Boolean(), nullable=True),
        sa.Column('can_copy', sa.Boolean(), nullable=True),
        sa.Column('can_upload_sds', sa.Boolean(), nullable=True),
        sa.Column('can_add_location', sa.Boolean(), nullable=True),
        sa.Column('can_delete_location', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )

    op.create_table(
        'substances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('cas', sa.Text(), nullable=True),
        sa.Column('ec_number', sa.Text(), nullable=True),
        sa.Column('classification', sa.Text(), nullable=True),
        sa.Column('h_phrases', sa.Text(), nullable=True),
        sa.Column('scl_mfactor', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('is_cmr', sa.Boolean(), nullable=True),
        sa.Column('sds_filename', sa.String(length=255), nullable=True),
        sa.Column('sds_upload_timestamp', sa.DateTime(), nullable=True),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('physical_location', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], name='fk_substances_location_id'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'sds_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('substance_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('manufacturer', sa.String(length=255), nullable=True),
        sa.Column('upload_timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['substance_id'], ['substances.id'], name='fk_sds_files_substance_id'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=80), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_audit_log_user_id'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('audit_log')
    op.drop_table('sds_files')
    op.drop_table('substances')
    op.drop_table('users')
    op.drop_table('locations')

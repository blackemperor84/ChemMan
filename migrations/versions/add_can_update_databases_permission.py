"""Add can_update_databases column to users table

Revision ID: add_update_db_perm
Revises: 779a32f7cb24
Create Date: 2026-01-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_update_db_perm'
down_revision = '779a32f7cb24'
branch_labels = None
depends_on = None


def upgrade():
    # Add can_update_databases column to users table
    op.add_column('users', sa.Column('can_update_databases', sa.Boolean(), nullable=True))

    # Set default value to False for existing rows (PostgreSQL uses FALSE, SQLite uses 0)
    op.execute('UPDATE users SET can_update_databases = FALSE WHERE can_update_databases IS NULL')


def downgrade():
    # Remove the column if rolling back
    op.drop_column('users', 'can_update_databases')

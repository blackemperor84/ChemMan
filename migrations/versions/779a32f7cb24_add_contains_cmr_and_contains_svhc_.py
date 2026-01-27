"""Add contains_cmr and contains_svhc columns

Revision ID: 779a32f7cb24
Revises: add_org_unit_2025
Create Date: 2026-01-18 20:20:49.272182

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '779a32f7cb24'
down_revision = 'add_org_unit_2025'
branch_labels = None
depends_on = None


def upgrade():
    # Add contains_cmr column to substances table
    op.add_column('substances', sa.Column('contains_cmr', sa.Boolean(), nullable=True))
    # Add contains_svhc column to substances table
    op.add_column('substances', sa.Column('contains_svhc', sa.Boolean(), nullable=True))

    # Set default values to False for existing rows
    op.execute('UPDATE substances SET contains_cmr = 0 WHERE contains_cmr IS NULL')
    op.execute('UPDATE substances SET contains_svhc = 0 WHERE contains_svhc IS NULL')


def downgrade():
    # Remove the columns if rolling back
    op.drop_column('substances', 'contains_svhc')
    op.drop_column('substances', 'contains_cmr')

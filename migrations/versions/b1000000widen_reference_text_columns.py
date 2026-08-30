"""Poszerzenie kolumn tekstowych w tabelach referencyjnych (CLP, SVHC) do TEXT

Revision ID: widen_ref_text
Revises: add_update_db_perm
Create Date: 2026-08-24

Powód
-----
Migracje '0c94b152b44c' i 'eba4b0241b18' tworzyły kolumny jako
VARCHAR(255)/VARCHAR(20), podczas gdy modele deklarują db.Text:

    excel_source_substances.name / cas / ec_number
    svhc_substances.name / cas / ec_number

SQLite nie egzekwuje długości VARCHAR, więc rozbieżność była niewidoczna lokalnie.
Na PostgreSQL baza zbudowana z migracji odrzuciłaby import CLP/SVHC błędem
"value too long for type character varying(20)" - dane ECHA zawierają nazwy do
ok. 2048 znaków oraz listy numerów CAS/EC do ok. 484 znaków.

Ta migracja doprowadza schemat zbudowany z migracji do zgodności z modelami.
Zmiana jest wyłącznie poszerzająca, więc nie może obciąć istniejących danych.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'widen_ref_text'
down_revision = 'add_update_db_perm'
branch_labels = None
depends_on = None


# (tabela, kolumna, poprzedni typ) - poprzedni typ potrzebny tylko do downgrade
_COLUMNS = [
    ('excel_source_substances', 'name', sa.String(length=255)),
    ('excel_source_substances', 'cas', sa.String(length=20)),
    ('excel_source_substances', 'ec_number', sa.String(length=20)),
    ('svhc_substances', 'name', sa.String(length=255)),
    ('svhc_substances', 'cas', sa.String(length=20)),
    ('svhc_substances', 'ec_number', sa.String(length=20)),
]


def upgrade():
    # batch_alter_table jest wymagane dla SQLite (brak ALTER COLUMN TYPE);
    # na PostgreSQL wykona zwykłe ALTER TABLE ... TYPE TEXT.
    for table, column, old_type in _COLUMNS:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=old_type,
                type_=sa.Text(),
                existing_nullable=True,
            )


def downgrade():
    # Uwaga: zwężenie może obciąć dane dłuższe niż limit.
    for table, column, old_type in _COLUMNS:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                column,
                existing_type=sa.Text(),
                type_=old_type,
                existing_nullable=True,
            )

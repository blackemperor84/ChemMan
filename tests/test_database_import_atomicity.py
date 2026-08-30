"""
Testy atomowości importu baz referencyjnych (CLP, SVHC).

Pokrywa problem z audytu: import wykonywał DELETE + commit, a dopiero potem
INSERT. Nieudany insert zostawiał pustą tabelę referencyjną bez możliwości
odtworzenia danych - rollback nie cofał już zatwierdzonego DELETE.
"""
import io

import pandas as pd
import pytest

from models import db, ExcelSourceSubstance, SVHCSubstance
from utils.database_import import import_clp_data, import_svhc_data


def make_clp_excel(rows):
    """
    Buduje w pamięci plik CLP w układzie oczekiwanym przez validate_clp_excel
    (nagłówek w wierszu 0, wiersz 1 pomijany).
    """
    header = [
        'International Chemical Identification', 'CAS No', 'EC No',
        'Classification', 'Unnamed: 5', 'Specific Conc. Limits, M-factors',
    ]
    data = [['(pomijany wiersz)'] * len(header)]
    data.extend(rows)

    buffer = io.BytesIO()
    pd.DataFrame(data, columns=header).to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


def make_svhc_excel(rows):
    """Buduje w pamięci plik SVHC z polskimi nagłówkami."""
    header = ['Nazwa substancji', 'Nr CAS', 'Nr WE', 'Powód włączenia', 'Data włączenia']
    buffer = io.BytesIO()
    pd.DataFrame(rows, columns=header).to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer


@pytest.fixture
def existing_clp_rows(db_session):
    """Dane referencyjne CLP, które import mógłby bezpowrotnie skasować."""
    rows = [
        ExcelSourceSubstance(name='Stara Substancja A', cas='100-00-1',
                             ec_number='200-000-1', classification='Flam. Liq. 2',
                             h_phrases='H225', scl_mfactor='M=10'),
        ExcelSourceSubstance(name='Stara Substancja B', cas='100-00-2',
                             ec_number='200-000-2', classification='Acute Tox. 3',
                             h_phrases='H301', scl_mfactor=None),
    ]
    db_session.add_all(rows)
    db_session.commit()
    return rows


@pytest.fixture
def existing_svhc_rows(db_session):
    rows = [
        SVHCSubstance(name='Stary SVHC A', cas='200-00-1', ec_number='300-000-1',
                      reason='Article 57a', date_inclusion='2015-01-01'),
        SVHCSubstance(name='Stary SVHC B', cas='200-00-2', ec_number='300-000-2',
                      reason='Article 57c', date_inclusion='2016-01-01'),
    ]
    db_session.add_all(rows)
    db_session.commit()
    return rows


class TestClpImportAtomicity:

    def test_failed_insert_preserves_existing_data(self, app, db_session, existing_clp_rows, monkeypatch):
        """
        Najważniejszy przypadek: insert wybucha w połowie podmiany.
        Stare rekordy muszą przetrwać.
        """
        def explode(*args, **kwargs):
            raise RuntimeError('symulowana awaria bazy w trakcie insertu')

        monkeypatch.setattr(db.session, 'bulk_insert_mappings', explode)

        excel = make_clp_excel([['Nowa Substancja', '999-99-9', '999-999-9',
                                'Skin Corr. 1A', 'H314', None]])
        success, message, count = import_clp_data(excel)

        assert success is False
        assert count == 0

        db.session.rollback()
        remaining = ExcelSourceSubstance.query.order_by(ExcelSourceSubstance.name).all()
        assert len(remaining) == 2, "Nieudany import skasował bazę referencyjną CLP"
        assert [r.name for r in remaining] == ['Stara Substancja A', 'Stara Substancja B']
        assert remaining[0].scl_mfactor == 'M=10', "Utracono kurowane dane SCL/M-factor"

    def test_successful_import_replaces_data(self, app, db_session, existing_clp_rows):
        """Regresja: udany import nadal podmienia zawartość tabeli."""
        excel = make_clp_excel([
            ['Nowa Substancja 1', '999-99-1', '999-999-1', 'Skin Corr. 1A', 'H314', None],
            ['Nowa Substancja 2', '999-99-2', '999-999-2', 'Eye Dam. 1', 'H318', None],
        ])
        success, message, count = import_clp_data(excel)

        assert success is True, message
        assert count == 2

        names = sorted(r.name for r in ExcelSourceSubstance.query.all())
        assert names == ['Nowa Substancja 1', 'Nowa Substancja 2']

    def test_empty_dataset_does_not_wipe_database(self, app, db_session, existing_clp_rows):
        """Plik bez rekordów nie może wyczyścić bazy referencyjnej."""
        excel = make_clp_excel([])
        success, message, count = import_clp_data(excel)

        assert success is False
        assert count == 0
        assert ExcelSourceSubstance.query.count() == 2, "Pusty plik skasował bazę CLP"


class TestSvhcImportAtomicity:

    def test_failed_insert_preserves_existing_data(self, app, db_session, existing_svhc_rows, monkeypatch):
        def explode(*args, **kwargs):
            raise RuntimeError('symulowana awaria bazy w trakcie insertu')

        monkeypatch.setattr(db.session, 'bulk_insert_mappings', explode)

        excel = make_svhc_excel([['Nowy SVHC', '888-88-8', '888-888-8',
                                 'Article 57f', '2026-01-01']])
        success, message, count = import_svhc_data(excel)

        assert success is False
        assert count == 0

        db.session.rollback()
        remaining = SVHCSubstance.query.order_by(SVHCSubstance.name).all()
        assert len(remaining) == 2, "Nieudany import skasował bazę referencyjną SVHC"
        assert [r.name for r in remaining] == ['Stary SVHC A', 'Stary SVHC B']
        assert remaining[0].reason == 'Article 57a', "Utracono powód włączenia SVHC"

    def test_successful_import_replaces_data(self, app, db_session, existing_svhc_rows):
        """Regresja: udany import nadal podmienia zawartość tabeli."""
        excel = make_svhc_excel([
            ['Nowy SVHC 1', '888-88-1', '888-888-1', 'Article 57f', '2026-01-01'],
            ['Nowy SVHC 2', '888-88-2', '888-888-2', 'Article 57a', '2026-02-01'],
        ])
        success, message, count = import_svhc_data(excel)

        assert success is True, message
        assert count == 2

        names = sorted(r.name for r in SVHCSubstance.query.all())
        assert names == ['Nowy SVHC 1', 'Nowy SVHC 2']

    def test_empty_dataset_does_not_wipe_database(self, app, db_session, existing_svhc_rows):
        excel = make_svhc_excel([])
        success, message, count = import_svhc_data(excel)

        assert success is False
        assert count == 0
        assert SVHCSubstance.query.count() == 2, "Pusty plik skasował bazę SVHC"

"""Regression tests for the four issues found in the follow-up review of 9b9dfd6.

1. CSV formula injection through the CAS/EC identifier cells, which the first
   csv_safe pass deliberately skipped because they were built as ="..." literals.
2. A failed SVHC verification persisting is_svhc=False as if it were a checked
   negative result.
3. Unchecked manual checkboxes being treated as a deliberate override, wiping out
   automatic CMR/SVHC detection.
4. SDS upload cleanup deleting a file whose database row had already committed.
"""
import csv
import io
import os

import pytest

from models import SDSFile, Substance, db


def login_admin(client):
    return client.post('/login', data={'username': 'admin', 'password': 'adminpassword123'})


class TestCsvIdentifierInjection:
    """A quote inside CAS/EC used to break out of the ="..." literal."""

    PAYLOAD = '"&SUM(1,1)&"'

    def _export_cells(self, client, url, column):
        response = client.get(url)
        assert response.status_code == 200
        text = response.data.decode('utf-8-sig')
        rows = list(csv.reader(io.StringIO(text)))
        assert len(rows) > 1, 'export produced no data rows'
        return [r[column] for r in rows[1:] if len(r) > column]

    def test_cas_cannot_produce_a_formula_in_all_export(
        self, client, admin_user, test_location, db_session
    ):
        db_session.add(Substance(name='Injection CAS', cas=self.PAYLOAD,
                                 location_id=test_location.id))
        db_session.commit()
        login_admin(client)

        for cell in self._export_cells(client, '/export/all/csv', 1):
            assert not cell.startswith('='), f'formula cell produced: {cell!r}'

    def test_ec_cannot_produce_a_formula_in_all_export(
        self, client, admin_user, test_location, db_session
    ):
        db_session.add(Substance(name='Injection EC', cas='111-11-1',
                                 ec_number=self.PAYLOAD, location_id=test_location.id))
        db_session.commit()
        login_admin(client)

        for cell in self._export_cells(client, '/export/all/csv', 2):
            assert not cell.startswith('='), f'formula cell produced: {cell!r}'

    def test_cas_cannot_produce_a_formula_in_location_export(
        self, client, admin_user, test_location, db_session
    ):
        db_session.add(Substance(name='Injection loc', cas=self.PAYLOAD,
                                 location_id=test_location.id))
        db_session.commit()
        login_admin(client)

        url = f'/export/location/{test_location.id}/csv'
        for cell in self._export_cells(client, url, 1):
            assert not cell.startswith('='), f'formula cell produced: {cell!r}'

    def test_plain_identifiers_survive_unchanged(
        self, client, admin_user, test_location, db_session
    ):
        """The escaping must not mangle ordinary CAS numbers."""
        db_session.add(Substance(name='Ordinary', cas='7439-92-1',
                                 ec_number='231-100-4', location_id=test_location.id))
        db_session.commit()
        login_admin(client)

        cas_cells = self._export_cells(client, '/export/all/csv', 1)
        assert '7439-92-1' in cas_cells


class TestUnverifiedSvhcIsNotPersisted:
    """A lookup failure must never be recorded as 'checked, not on the list'."""

    @pytest.fixture
    def broken_svhc(self, monkeypatch):
        import utils

        class Boom:
            @property
            def query(self):
                raise RuntimeError('svhc table unavailable')

        monkeypatch.setattr(utils, 'SVHCSubstance', Boom())

    def test_excel_add_is_rejected(self, client, admin_user, test_location,
                                   db_session, broken_svhc):
        login_admin(client)
        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json={'name': 'Nieweryfikowalna', 'cas': '123-45-6'},
        )

        assert response.status_code == 503
        assert Substance.query.filter_by(name='Nieweryfikowalna').first() is None

    def test_manual_add_is_rejected_when_user_gave_no_flag(
        self, client, admin_user, test_location, db_session, broken_svhc
    ):
        login_admin(client)
        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json={'name': 'Reczna bez flagi', 'cas': '123-45-7'},
        )

        assert response.status_code == 503
        assert Substance.query.filter_by(name='Reczna bez flagi').first() is None

    def test_manual_add_succeeds_when_user_sets_the_flag(
        self, client, admin_user, test_location, db_session, broken_svhc
    ):
        """An explicit human decision does not need the automatic lookup."""
        login_admin(client)
        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json={'name': 'Reczna z flaga', 'cas': '123-45-8', 'is_svhc': True},
        )

        assert response.status_code == 200
        saved = Substance.query.filter_by(name='Reczna z flaga').first()
        assert saved is not None
        assert saved.is_svhc is True


class TestCheckboxesDoNotOverrideDetection:
    """An untouched checkbox must not erase automatic classification."""

    def test_unchecked_cmr_does_not_clear_classification_detection(
        self, client, admin_user, test_location, db_session
    ):
        login_admin(client)
        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json={
                'name': 'Carc bez zwrotow H',
                'cas': '222-22-2',
                'classification': 'Carc. 1B',
                'h_phrases': '',
                # what the old client sent for untouched boxes:
                'is_cmr': False,
                'is_svhc': False,
            },
        )
        assert response.status_code == 200

        saved = Substance.query.filter_by(name='Carc bez zwrotow H').first()
        assert saved is not None
        assert saved.is_cmr is True, 'auto-detected CMR was wiped by an untouched checkbox'

    def test_unchecked_cmr_does_not_clear_h_phrase_detection(
        self, client, admin_user, test_location, db_session
    ):
        login_admin(client)
        client.post(
            f'/location/{test_location.id}/add_manual',
            json={'name': 'H350 bez zaznaczenia', 'cas': '222-22-3',
                  'h_phrases': 'H350', 'is_cmr': False},
        )

        saved = Substance.query.filter_by(name='H350 bez zaznaczenia').first()
        assert saved is not None
        assert saved.is_cmr is True

    def test_checkbox_can_still_add_a_flag(
        self, client, admin_user, test_location, db_session
    ):
        login_admin(client)
        client.post(
            f'/location/{test_location.id}/add_manual',
            json={'name': 'Recznie oznaczona', 'cas': '222-22-4',
                  'h_phrases': 'H319', 'is_cmr': True},
        )

        saved = Substance.query.filter_by(name='Recznie oznaczona').first()
        assert saved is not None
        assert saved.is_cmr is True

    def test_non_hazardous_stays_unflagged(
        self, client, admin_user, test_location, db_session
    ):
        login_admin(client)
        client.post(
            f'/location/{test_location.id}/add_manual',
            json={'name': 'Nieszkodliwa', 'cas': '222-22-5',
                  'h_phrases': 'H319', 'classification': 'Eye Irrit. 2',
                  'is_cmr': False},
        )

        saved = Substance.query.filter_by(name='Nieszkodliwa').first()
        assert saved is not None
        assert saved.is_cmr is False


class TestPostCommitFailureKeepsFile:
    """Cleanup must stop once the row is committed."""

    def test_failure_after_commit_does_not_delete_the_pdf(
        self, app, client, admin_user, test_location, db_session, monkeypatch
    ):
        substance = Substance(name='SDS post-commit', cas='888-88-8',
                              location_id=test_location.id)
        db_session.add(substance)
        db_session.commit()

        # Blow up after the commit, in the audit-logging step.
        import routes.files as files_module

        def boom(*args, **kwargs):
            raise RuntimeError('post-commit failure')

        monkeypatch.setattr(files_module, 'log_action', boom)

        login_admin(client)
        client.post(
            f'/substance/{substance.id}/upload_sds',
            data={'sds_file': (io.BytesIO(b'%PDF-1.4 fake pdf content'), 'karta.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        monkeypatch.undo()

        row = SDSFile.query.filter_by(substance_id=substance.id).first()
        assert row is not None, 'row should have survived - it was committed'

        path = os.path.join(app.config['UPLOAD_FOLDER'], row.filename)
        assert os.path.exists(path), 'committed row lost its file to cleanup'
        os.remove(path)

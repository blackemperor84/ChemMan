"""Tests for audit-log and file/DB transactional integrity.

Covers:
- log_action(commit=False) participating in the caller's transaction
- log_action(commit=True) rolling back a poisoned session instead of leaving it broken
- SDS upload not leaving an orphan file when the DB write fails
- SDS delete not leaving a DB row pointing at a missing file
"""
import io
import os

import pytest

from models import AuditLog, Location, SDSFile, Substance, db
from utils import log_action


class TestLogActionCommitFlag:
    def test_commit_false_does_not_commit(self, app, db_session, admin_user):
        """The entry must be pending, so the caller's rollback can discard it."""
        with app.test_request_context():
            from flask_login import login_user
            login_user(admin_user)

            log_action('TEST_ATOMIC', target_type='Substance', target_id=1, commit=False)

            # Still uncommitted: rolling back the caller's transaction drops it.
            db.session.rollback()
            assert AuditLog.query.filter_by(action='TEST_ATOMIC').first() is None

    def test_commit_false_is_persisted_by_caller_commit(self, app, db_session, admin_user):
        with app.test_request_context():
            from flask_login import login_user
            login_user(admin_user)

            log_action('TEST_ATOMIC_OK', target_type='Substance', target_id=1, commit=False)
            db.session.commit()

            assert AuditLog.query.filter_by(action='TEST_ATOMIC_OK').first() is not None

    def test_commit_true_persists_immediately(self, app, db_session, admin_user):
        with app.test_request_context():
            from flask_login import login_user
            login_user(admin_user)

            log_action('TEST_STANDALONE', target_type='Substance', target_id=1)

            db.session.rollback()  # must not undo it
            assert AuditLog.query.filter_by(action='TEST_STANDALONE').first() is not None

    def test_commit_false_propagates_failure(self, app, db_session, admin_user, monkeypatch):
        """With commit=False the caller's transaction is still open, so it must see the error."""
        with app.test_request_context():
            from flask_login import login_user
            login_user(admin_user)

            def boom(*args, **kwargs):
                raise RuntimeError('session is broken')

            monkeypatch.setattr(db.session, 'add', boom)

            with pytest.raises(RuntimeError):
                log_action('TEST_RAISES', commit=False)

    def test_commit_true_swallows_but_rolls_back(self, app, db_session, admin_user, monkeypatch):
        """A failed audit write must not leave the session poisoned for the caller."""
        with app.test_request_context():
            from flask_login import login_user
            login_user(admin_user)

            calls = {'rollback': 0}
            real_rollback = db.session.rollback

            def counting_rollback():
                calls['rollback'] += 1
                return real_rollback()

            def boom():
                raise RuntimeError('commit failed')

            monkeypatch.setattr(db.session, 'commit', boom)
            monkeypatch.setattr(db.session, 'rollback', counting_rollback)

            # Must not raise - the caller's action is already durable.
            log_action('TEST_SWALLOWED')

            assert calls['rollback'] == 1


class TestSDSUploadAtomicity:
    def _login(self, client):
        client.post('/login', data={'username': 'admin', 'password': 'adminpassword123'})

    def test_failed_db_write_leaves_no_orphan_file(
        self, app, client, admin_user, test_location, db_session, monkeypatch
    ):
        """If the commit fails after the file is written, the file must be removed."""
        substance = Substance(name='SDS orphan test', cas='555-55-5',
                              location_id=test_location.id)
        db_session.add(substance)
        db_session.commit()

        upload_folder = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        before = set(os.listdir(upload_folder))

        def boom():
            raise RuntimeError('commit failed')

        monkeypatch.setattr(db.session, 'commit', boom)

        self._login(client)
        client.post(
            f'/substance/{substance.id}/upload_sds',
            data={
                'sds_file': (io.BytesIO(b'%PDF-1.4 fake pdf content'), 'karta.pdf'),
                'manufacturer': 'ACME',
            },
            content_type='multipart/form-data',
            follow_redirects=True,
        )

        monkeypatch.undo()
        after = set(os.listdir(upload_folder))
        assert after == before, f'Orphan file left behind: {after - before}'

    def test_successful_upload_keeps_file_and_row(
        self, app, client, admin_user, test_location, db_session
    ):
        substance = Substance(name='SDS happy path', cas='556-55-5',
                              location_id=test_location.id)
        db_session.add(substance)
        db_session.commit()

        self._login(client)
        client.post(
            f'/substance/{substance.id}/upload_sds',
            data={
                'sds_file': (io.BytesIO(b'%PDF-1.4 fake pdf content'), 'karta.pdf'),
                'manufacturer': 'ACME',
            },
            content_type='multipart/form-data',
            follow_redirects=True,
        )

        row = SDSFile.query.filter_by(substance_id=substance.id).first()
        assert row is not None
        path = os.path.join(app.config['UPLOAD_FOLDER'], row.filename)
        assert os.path.exists(path)
        os.remove(path)


class TestSDSDeleteOrdering:
    def _login(self, client):
        client.post('/login', data={'username': 'admin', 'password': 'adminpassword123'})

    def test_failed_db_delete_keeps_file_on_disk(
        self, app, client, admin_user, test_location, db_session, monkeypatch
    ):
        """A dangling DB row pointing at a missing file is the worse failure.

        If the DB delete cannot commit, the file must still be on disk so the
        existing row keeps working.
        """
        substance = Substance(name='SDS delete test', cas='557-55-5',
                              location_id=test_location.id)
        db_session.add(substance)
        db_session.commit()

        upload_folder = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filename = 'delete_ordering_test.pdf'
        path = os.path.join(upload_folder, filename)
        with open(path, 'wb') as fh:
            fh.write(b'%PDF-1.4 fake')

        sds = SDSFile(substance_id=substance.id, filename=filename,
                      original_filename='karta.pdf')
        db_session.add(sds)
        db_session.commit()
        sds_id = sds.id

        def boom():
            raise RuntimeError('commit failed')

        monkeypatch.setattr(db.session, 'commit', boom)

        self._login(client)
        client.post(
            f'/substance/{substance.id}/delete_sds/{sds_id}',
            follow_redirects=True,
        )

        monkeypatch.undo()
        db.session.rollback()

        # The row survived, so the file it points at must survive too.
        assert db.session.get(SDSFile, sds_id) is not None
        assert os.path.exists(path), 'File deleted while its DB row still exists'

        os.remove(path)

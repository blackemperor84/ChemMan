"""
Integration tests for file routes.
Tests file upload, download, and deletion with security validations.
"""
import pytest
import os
import io
from flask import url_for
from models import db, User, Location, Substance


def create_pdf_file(size_mb=1):
    """
    Create a fake PDF file for testing.

    Args:
        size_mb: Size of file in megabytes

    Returns:
        BytesIO: File-like object containing PDF data
    """
    # PDF magic number
    pdf_header = b'%PDF-1.4\n'
    # Add some content to reach desired size
    content_size = int((size_mb * 1024 * 1024) - len(pdf_header))
    content = b'A' * content_size

    pdf_data = pdf_header + content
    return io.BytesIO(pdf_data)


def create_fake_file(content=b'Not a PDF', filename='test.pdf'):
    """
    Create a fake file with arbitrary content.

    Args:
        content: Byte content of the file
        filename: Name of the file

    Returns:
        BytesIO: File-like object
    """
    file_obj = io.BytesIO(content)
    file_obj.name = filename
    return file_obj


class TestUploadSDS:
    """Tests for uploading SDS files (POST /substance/<id>/upload_sds)."""

    def test_upload_requires_login(self, client, test_substance):
        """Test that uploading SDS requires authentication."""
        pdf_file = create_pdf_file()

        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'test.pdf')},
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_upload_requires_permission(self, client, db_session, test_substance):
        """Test that uploading SDS requires upload_sds permission."""
        # Create user without upload permission
        user = User(username='noupload')
        user.set_password('password123')
        user.can_view = True
        user.can_upload_sds = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'noupload',
            'password': 'password123'
        })

        pdf_file = create_pdf_file()
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'test.pdf')},
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect away

    def test_upload_success(self, client, admin_user, test_substance, app):
        """Test successful SDS file upload."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        pdf_file = create_pdf_file()
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'safety_data_sheet.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify in database
        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            assert substance.sds_filename is not None
            assert substance.sds_filename.endswith('safety_data_sheet.pdf')
            assert substance.sds_upload_timestamp is not None

    def test_upload_no_file_selected(self, client, admin_user, test_substance):
        """Test upload fails when no file is selected."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={},
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'nie wybrano' in data or 'no file' in data

    def test_upload_empty_filename(self, client, admin_user, test_substance):
        """Test upload fails when filename is empty."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Create file with empty filename
        pdf_file = create_pdf_file()
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, '')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'nie wybrano' in data or 'no file' in data

    def test_upload_invalid_extension(self, client, admin_user, test_substance):
        """Test upload fails with invalid file extension."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Try to upload .txt file
        fake_file = create_fake_file(b'Some text content', 'document.txt')
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (fake_file, 'document.txt')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'niedozwolony' in data or 'not allowed' in data or 'dozwolone' in data

    def test_upload_file_too_large(self, client, admin_user, test_substance):
        """Test upload fails when file exceeds size limit (16MB)."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Create 17MB file (exceeds 16MB limit)
        large_file = create_pdf_file(size_mb=17)
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (large_file, 'large.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        # Flask returns 413 Request Entity Too Large before route handler
        assert response.status_code == 413

    def test_upload_invalid_mime_type(self, client, admin_user, test_substance):
        """Test upload fails with invalid MIME type (not a real PDF)."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Create fake file with .pdf extension but not PDF content
        fake_pdf = create_fake_file(b'This is not a PDF file!', 'fake.pdf')
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (fake_pdf, 'fake.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'nie jest prawidłowym' in data or 'not a valid' in data or 'pdf' in data

    def test_upload_replaces_old_file(self, client, admin_user, test_substance, app):
        """Test that uploading new file replaces old one."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Upload first file
        pdf_file1 = create_pdf_file()
        client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file1, 'first.pdf')},
            content_type='multipart/form-data'
        )

        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            old_filename = substance.sds_filename

        # Upload second file
        pdf_file2 = create_pdf_file()
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file2, 'second.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify new filename is different
        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            assert substance.sds_filename != old_filename
            assert substance.sds_filename.endswith('second.pdf')

    def test_upload_updates_location_timestamp(self, client, admin_user, test_substance, test_location, app):
        """Test that uploading updates location's last_modified timestamp."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Get original timestamp
        original_modified = test_location.last_modified

        pdf_file = create_pdf_file()
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'test.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify timestamp was updated
        with app.app_context():
            location = Location.query.get(test_location.id)
            assert location.last_modified > original_modified

    def test_upload_logs_action(self, client, admin_user, test_substance, app):
        """Test that uploading logs an audit action."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        pdf_file = create_pdf_file()
        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'audit_test.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify audit log
        with app.app_context():
            from models import AuditLog
            log = AuditLog.query.filter_by(action='UPLOAD_SDS').order_by(AuditLog.timestamp.desc()).first()
            assert log is not None
            assert log.target_type == 'Substance'
            assert log.target_id == test_substance.id

    def test_upload_substance_not_found(self, client, admin_user):
        """Test upload fails for non-existent substance."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        pdf_file = create_pdf_file()
        response = client.post(
            '/substance/99999/upload_sds',
            data={'sds_file': (pdf_file, 'test.pdf')},
            content_type='multipart/form-data',
            follow_redirects=False
        )

        assert response.status_code in [404, 500, 302]  # get_or_404 behavior


class TestDownloadSDS:
    """Tests for downloading SDS files (GET /uploads/sds/<filename>)."""

    def test_download_requires_login(self, client):
        """Test that downloading SDS requires authentication."""
        response = client.get('/uploads/sds/test.pdf', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_download_requires_permission(self, client, db_session):
        """Test that downloading SDS requires view permission."""
        # Create user without view permission
        user = User(username='noview')
        user.set_password('password123')
        user.can_view = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'noview',
            'password': 'password123'
        })

        response = client.get('/uploads/sds/test.pdf', follow_redirects=False)
        assert response.status_code == 302  # Redirect away

    def test_download_file_not_found(self, client, admin_user):
        """Test download fails when file doesn't exist."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/uploads/sds/nonexistent.pdf')
        # send_from_directory raises exception, caught by error handler
        assert response.status_code in [404, 500]

    def test_download_path_traversal_double_dot(self, client, admin_user):
        """Test path traversal protection with '..'."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/uploads/sds/../../../etc/passwd')
        # Path traversal protection should abort with 403 or 500
        assert response.status_code in [403, 500]

    def test_download_path_traversal_absolute(self, client, admin_user):
        """Test path traversal protection with absolute path."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/uploads/sds//etc/passwd')
        # Path traversal causes redirect or error (308 redirect, 403, 404, or 500)
        assert response.status_code in [308, 403, 404, 500]

    def test_download_success(self, client, admin_user, test_substance, app):
        """Test successful file download."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # First upload a file
        pdf_file = create_pdf_file(size_mb=0.1)  # Small file for testing
        client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'download_test.pdf')},
            content_type='multipart/form-data'
        )

        # Get the filename from database
        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            filename = substance.sds_filename

        # Download the file
        response = client.get(f'/uploads/sds/{filename}')

        # Should succeed
        assert response.status_code == 200
        # Should be PDF
        assert response.content_type == 'application/pdf'
        # Should have attachment header
        assert 'attachment' in response.headers.get('Content-Disposition', '')


class TestDeleteSDS:
    """Tests for deleting SDS files (POST /substance/<id>/delete_sds)."""

    def test_delete_requires_login(self, client, test_substance):
        """Test that deleting SDS requires authentication."""
        response = client.post(
            f'/substance/{test_substance.id}/delete_sds',
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_delete_requires_permission(self, client, db_session, test_substance):
        """Test that deleting SDS requires upload_sds permission."""
        # Create user without upload permission
        user = User(username='nodelete')
        user.set_password('password123')
        user.can_view = True
        user.can_upload_sds = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'nodelete',
            'password': 'password123'
        })

        response = client.post(
            f'/substance/{test_substance.id}/delete_sds',
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect away

    def test_delete_no_file_attached(self, client, admin_user, test_substance):
        """Test delete when no file is attached to substance."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Ensure no file is attached
        test_substance.sds_filename = None

        response = client.post(
            f'/substance/{test_substance.id}/delete_sds',
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'brak' in data or 'no file' in data or 'warning' in data

    def test_delete_success(self, client, admin_user, test_substance, app):
        """Test successful SDS file deletion."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # First upload a file
        pdf_file = create_pdf_file(size_mb=0.1)
        client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'to_delete.pdf')},
            content_type='multipart/form-data'
        )

        # Verify file was uploaded
        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            assert substance.sds_filename is not None
            filename = substance.sds_filename

        # Delete the file
        response = client.post(
            f'/substance/{test_substance.id}/delete_sds',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify file was deleted from database
        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            assert substance.sds_filename is None
            assert substance.sds_upload_timestamp is None

    def test_delete_updates_location_timestamp(self, client, admin_user, test_substance, test_location, app):
        """Test that deleting updates location's last_modified timestamp."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Upload a file first
        pdf_file = create_pdf_file(size_mb=0.1)
        client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'test.pdf')},
            content_type='multipart/form-data'
        )

        with app.app_context():
            location = Location.query.get(test_location.id)
            original_modified = location.last_modified

        # Delete the file
        response = client.post(
            f'/substance/{test_substance.id}/delete_sds',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify timestamp was updated
        with app.app_context():
            location = Location.query.get(test_location.id)
            assert location.last_modified > original_modified

    def test_delete_logs_action(self, client, admin_user, test_substance, app):
        """Test that deleting logs an audit action."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Upload a file first
        pdf_file = create_pdf_file(size_mb=0.1)
        client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (pdf_file, 'audit_delete.pdf')},
            content_type='multipart/form-data'
        )

        # Delete the file
        response = client.post(
            f'/substance/{test_substance.id}/delete_sds',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify audit log
        with app.app_context():
            from models import AuditLog
            log = AuditLog.query.filter_by(action='DELETE_SDS').order_by(AuditLog.timestamp.desc()).first()
            assert log is not None
            assert log.target_type == 'Substance'
            assert log.target_id == test_substance.id

    def test_delete_substance_not_found(self, client, admin_user):
        """Test delete fails for non-existent substance."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substance/99999/delete_sds',
            follow_redirects=False
        )

        assert response.status_code in [404, 500, 302]  # get_or_404 behavior

"""
Integration tests for admin routes.
Tests user management and permission controls (security-critical).
"""
import pytest
from flask import url_for
from models import db, User, AuditLog


class TestListUsers:
    """Tests for listing users (GET /admin/users)."""

    def test_list_requires_login(self, client):
        """Test that listing users requires authentication."""
        response = client.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_list_requires_admin(self, client, db_session):
        """Test that listing users requires admin permission."""
        # Create non-admin user
        user = User(username='regular')
        user.set_password('password123')
        user.is_admin = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'regular',
            'password': 'password123'
        })

        response = client.get('/admin/users', follow_redirects=True)
        data = response.data.decode('utf-8').lower()
        assert 'nie masz uprawnień' in data or 'no permission' in data

    def test_list_success(self, client, admin_user):
        """Test successful user list retrieval."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/admin/users')
        assert response.status_code == 200
        assert b'admin' in response.data


class TestAddUser:
    """Tests for creating users (POST /admin/users/add)."""

    def test_add_requires_login(self, client):
        """Test that adding user requires authentication."""
        response = client.post('/admin/users/add',
            data={'new_username': 'newuser', 'new_password': 'password123'},
            follow_redirects=False
        )
        assert response.status_code == 302
        assert '/login' in response.location

    def test_add_requires_admin(self, client, db_session):
        """Test that adding user requires admin permission."""
        user = User(username='regular')
        user.set_password('password123')
        user.is_admin = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'regular',
            'password': 'password123'
        })

        response = client.post('/admin/users/add',
            data={'new_username': 'newuser', 'new_password': 'password123'},
            follow_redirects=True
        )
        data = response.data.decode('utf-8').lower()
        assert 'nie masz uprawnień' in data or 'no permission' in data

    def test_add_success(self, client, admin_user, app):
        """Test successful user creation."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/admin/users/add',
            data={
                'new_username': 'testuser',
                'new_password': 'testpass123',
                'can_view': 'on',
                'can_add': 'on'
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify user created
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            assert user is not None
            assert user.can_view is True
            assert user.can_add is True

    def test_add_empty_username_fails(self, client, admin_user):
        """Test that empty username fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/admin/users/add',
            data={'new_username': '', 'new_password': 'password123'},
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'wymagane' in data or 'required' in data

    def test_add_short_password_fails(self, client, admin_user):
        """Test that short password fails (< 8 chars)."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/admin/users/add',
            data={'new_username': 'newuser', 'new_password': 'short'},
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'co najmniej 8' in data or '8 znaków' in data or 'at least 8' in data

    def test_add_duplicate_username_fails(self, client, admin_user, db_session):
        """Test that duplicate username fails."""
        # Create existing user
        existing = User(username='existing')
        existing.set_password('password123')
        db_session.add(existing)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/admin/users/add',
            data={'new_username': 'existing', 'new_password': 'password123'},
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'istnieje' in data or 'exists' in data

    def test_add_logs_action(self, client, admin_user, app):
        """Test that adding user logs audit action."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/admin/users/add',
            data={
                'new_username': 'audituser',
                'new_password': 'password123'
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify audit log
        with app.app_context():
            log = AuditLog.query.filter_by(action='ADD_USER').order_by(AuditLog.timestamp.desc()).first()
            assert log is not None
            assert 'audituser' in log.details


class TestDeleteUser:
    """Tests for deleting users (POST /admin/users/<id>/delete)."""

    def test_delete_requires_login(self, client, db_session):
        """Test that deleting user requires authentication."""
        user = User(username='todelete')
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()

        response = client.post(f'/admin/users/{user.id}/delete',
            follow_redirects=False
        )
        assert response.status_code == 302
        assert '/login' in response.location

    def test_delete_requires_admin(self, client, db_session):
        """Test that deleting user requires admin permission."""
        regular = User(username='regular')
        regular.set_password('password123')
        regular.is_admin = False
        db_session.add(regular)

        todelete = User(username='todelete')
        todelete.set_password('password123')
        db_session.add(todelete)
        db_session.commit()

        client.post('/login', data={
            'username': 'regular',
            'password': 'password123'
        })

        response = client.post(f'/admin/users/{todelete.id}/delete',
            follow_redirects=True
        )
        data = response.data.decode('utf-8').lower()
        assert 'nie masz uprawnień' in data or 'no permission' in data

    def test_delete_success(self, client, admin_user, db_session, app):
        """Test successful user deletion."""
        user = User(username='deleteme')
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/admin/users/{user_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify user deleted
        with app.app_context():
            user = User.query.get(user_id)
            assert user is None

    def test_delete_admin_fails(self, client, admin_user, db_session):
        """Test that deleting 'admin' user fails."""
        # Get admin user ID
        admin_id = admin_user.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/admin/users/{admin_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'nie można usunąć' in data or 'cannot delete' in data

    def test_delete_not_found(self, client, admin_user):
        """Test deleting non-existent user."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/admin/users/99999/delete',
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'nie znaleziono' in data or 'not found' in data

    def test_delete_logs_action(self, client, admin_user, db_session, app):
        """Test that deleting user logs audit action."""
        user = User(username='auditdelete')
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/admin/users/{user_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify audit log
        with app.app_context():
            log = AuditLog.query.filter_by(action='DELETE_USER').order_by(AuditLog.timestamp.desc()).first()
            assert log is not None
            assert 'auditdelete' in log.details


class TestResetPassword:
    """Tests for resetting user passwords (POST /admin/users/<id>/reset_password)."""

    def test_reset_requires_login(self, client, db_session):
        """Test that resetting password requires authentication."""
        user = User(username='resetme')
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()

        response = client.post(f'/admin/users/{user.id}/reset_password',
            follow_redirects=False
        )
        assert response.status_code == 302
        assert '/login' in response.location

    def test_reset_requires_admin(self, client, db_session):
        """Test that resetting password requires admin permission."""
        regular = User(username='regular')
        regular.set_password('password123')
        regular.is_admin = False
        db_session.add(regular)

        resetme = User(username='resetme')
        resetme.set_password('password123')
        db_session.add(resetme)
        db_session.commit()

        client.post('/login', data={
            'username': 'regular',
            'password': 'password123'
        })

        response = client.post(f'/admin/users/{resetme.id}/reset_password',
            follow_redirects=True
        )
        data = response.data.decode('utf-8').lower()
        assert 'nie masz uprawnień' in data or 'no permission' in data

    def test_reset_success(self, client, admin_user, db_session):
        """Test successful password reset."""
        user = User(username='resetme')
        user.set_password('oldpassword123')
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/admin/users/{user.id}/reset_password',
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'hasło' in data or 'password' in data
        assert 'tymczasowe' in data or 'temporary' in data

    def test_reset_not_found(self, client, admin_user):
        """Test resetting password for non-existent user."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/admin/users/99999/reset_password',
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'nie znaleziono' in data or 'not found' in data

    def test_reset_logs_action(self, client, admin_user, db_session, app):
        """Test that resetting password logs audit action."""
        user = User(username='auditreset')
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/admin/users/{user_id}/reset_password',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify audit log
        with app.app_context():
            log = AuditLog.query.filter_by(action='RESET_PASSWORD').order_by(AuditLog.timestamp.desc()).first()
            assert log is not None
            assert 'auditreset' in log.details


class TestEditPermissions:
    """Tests for editing user permissions (POST /admin/users/<id>/edit_permissions)."""

    def test_edit_requires_login(self, client, db_session):
        """Test that editing permissions requires authentication."""
        user = User(username='editme')
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()

        response = client.post(f'/admin/users/{user.id}/edit_permissions',
            data={'can_view': 'on'},
            follow_redirects=False
        )
        assert response.status_code == 302
        assert '/login' in response.location

    def test_edit_requires_admin(self, client, db_session):
        """Test that editing permissions requires admin permission."""
        regular = User(username='regular')
        regular.set_password('password123')
        regular.is_admin = False
        db_session.add(regular)

        editme = User(username='editme')
        editme.set_password('password123')
        db_session.add(editme)
        db_session.commit()

        client.post('/login', data={
            'username': 'regular',
            'password': 'password123'
        })

        response = client.post(f'/admin/users/{editme.id}/edit_permissions',
            data={'can_view': 'on'},
            follow_redirects=True
        )
        data = response.data.decode('utf-8').lower()
        assert 'nie masz uprawnień' in data or 'no permission' in data

    def test_edit_success(self, client, admin_user, db_session, app):
        """Test successful permission update."""
        user = User(username='editme')
        user.set_password('password123')
        user.can_view = False
        user.can_add = False
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/admin/users/{user_id}/edit_permissions',
            data={'can_view': 'on', 'can_add': 'on'},
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify permissions updated
        with app.app_context():
            user = User.query.get(user_id)
            assert user.can_view is True
            assert user.can_add is True

    def test_edit_admin_user_fails(self, client, admin_user, db_session):
        """Test that editing admin user permissions fails."""
        admin_id = admin_user.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/admin/users/{admin_id}/edit_permissions',
            data={'can_view': 'on'},
            follow_redirects=True
        )

        assert response.status_code == 200
        data = response.data.decode('utf-8').lower()
        assert 'nie można modyfikować' in data or 'cannot modify' in data

    def test_edit_logs_action(self, client, admin_user, db_session, app):
        """Test that editing permissions logs audit action."""
        user = User(username='auditedit')
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/admin/users/{user_id}/edit_permissions',
            data={'can_view': 'on'},
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify audit log
        with app.app_context():
            log = AuditLog.query.filter_by(action='UPDATE_USER_PERMISSIONS').order_by(AuditLog.timestamp.desc()).first()
            assert log is not None
            assert 'auditedit' in log.details

"""
Integration tests for authentication routes.
Tests login, logout, and password change functionality.
"""
import pytest
from flask import url_for
from models import db, User


class TestLoginRoute:
    """Tests for the login route."""

    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()

    def test_already_authenticated_redirects(self, client, test_user):
        """Test that authenticated users are redirected from login page."""
        # Login first
        with client:
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword123'
            })
            # Try to access login page again
            response = client.get('/login', follow_redirects=False)
            assert response.status_code == 302
            # Should redirect away from login page (could be to '/' or '/locations')
            assert response.location in ['/', '/locations'] or 'locations' in response.location

    def test_login_with_empty_username(self, client, test_user):
        """Test login fails with empty username."""
        response = client.post('/login', data={
            'username': '',
            'password': 'testpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'wymagane' in response.data.lower() or b'required' in response.data.lower()

    def test_login_with_empty_password(self, client, test_user):
        """Test login fails with empty password."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'wymagane' in response.data.lower() or b'required' in response.data.lower()

    def test_login_with_whitespace_only(self, client, test_user):
        """Test login fails with whitespace-only credentials."""
        response = client.post('/login', data={
            'username': '   ',
            'password': '   '
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'wymagane' in response.data.lower() or b'required' in response.data.lower()

    def test_login_with_short_username(self, client, test_user):
        """Test login fails with username shorter than 3 characters."""
        response = client.post('/login', data={
            'username': 'ab',
            'password': 'testpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'3-50' in response.data or 'nieprawidłowa'.encode('utf-8') in response.data.lower()

    def test_login_with_long_username(self, client, test_user):
        """Test login fails with username longer than 50 characters."""
        response = client.post('/login', data={
            'username': 'a' * 51,
            'password': 'testpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'3-50' in response.data or 'nieprawidłowa'.encode('utf-8') in response.data.lower()

    def test_login_with_short_password(self, client, test_user):
        """Test login fails with password shorter than 8 characters."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'short'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'8' in response.data

    def test_login_with_valid_credentials(self, client, test_user):
        """Test successful login with valid credentials."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Witaj' in response.data or b'welcome' in response.data.lower()

    def test_login_with_invalid_username(self, client, test_user):
        """Test login fails with non-existent username."""
        response = client.post('/login', data={
            'username': 'nonexistentuser',
            'password': 'testpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'nieprawidłowa'.encode('utf-8') in response.data.lower() or b'invalid' in response.data.lower()

    def test_login_with_invalid_password(self, client, test_user):
        """Test login fails with incorrect password."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'nieprawidłowa'.encode('utf-8') in response.data.lower() or b'invalid' in response.data.lower()

    def test_login_with_next_parameter(self, client, test_user):
        """Test login redirects to 'next' parameter after successful login."""
        response = client.post('/login?next=/locations', data={
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/locations' in response.location

    def test_login_case_sensitive(self, client, test_user):
        """Test that login is case-sensitive for username."""
        response = client.post('/login', data={
            'username': 'TESTUSER',  # Different case
            'password': 'testpassword123'
        }, follow_redirects=True)
        # Should fail since username doesn't match exactly
        assert response.status_code == 200
        assert 'nieprawidłowa'.encode('utf-8') in response.data.lower() or b'invalid' in response.data.lower()

    def test_login_trims_whitespace(self, client, test_user):
        """Test that login trims leading/trailing whitespace."""
        response = client.post('/login', data={
            'username': '  testuser  ',
            'password': '  testpassword123  '
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'Witaj' in response.data or b'welcome' in response.data.lower()


class TestLogoutRoute:
    """Tests for the logout route."""

    def test_logout_requires_authentication(self, client):
        """Test that logout requires user to be logged in."""
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_logout_success(self, client, test_user):
        """Test successful logout."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        # Then logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert 'wylogowany'.encode('utf-8') in response.data.lower() or b'logged out' in response.data.lower()

    def test_logout_redirects_to_login(self, client, test_user):
        """Test that logout redirects to login page."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        # Then logout
        response = client.get('/logout', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_cannot_access_protected_route_after_logout(self, client, test_user):
        """Test that protected routes are inaccessible after logout."""
        # Login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        # Logout
        client.get('/logout')

        # Try to access protected route
        response = client.get('/change_password', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location


class TestChangePasswordRoute:
    """Tests for the change password route."""

    def test_change_password_requires_authentication(self, client):
        """Test that change password page requires login."""
        response = client.get('/change_password', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_change_password_page_loads(self, client, test_user):
        """Test that change password page loads for authenticated users."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.get('/change_password')
        assert response.status_code == 200
        assert b'password' in response.data.lower() or 'hasło'.encode('utf-8') in response.data.lower()

    def test_change_password_with_empty_fields(self, client, test_user):
        """Test change password fails with empty fields."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post('/change_password', data={
            'current_password': '',
            'new_password': '',
            'confirm_password': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'wymagane' in response.data.lower() or b'required' in response.data.lower()

    def test_change_password_with_incorrect_current(self, client, test_user):
        """Test change password fails with incorrect current password."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post('/change_password', data={
            'current_password': 'wrongpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'nieprawidłowe'.encode('utf-8') in response.data.lower() or b'incorrect' in response.data.lower()

    def test_change_password_with_short_new_password(self, client, test_user):
        """Test change password fails with short new password."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post('/change_password', data={
            'current_password': 'testpassword123',
            'new_password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'8' in response.data

    def test_change_password_with_long_new_password(self, client, test_user):
        """Test change password fails with excessively long password."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        long_password = 'a' * 129
        response = client.post('/change_password', data={
            'current_password': 'testpassword123',
            'new_password': long_password,
            'confirm_password': long_password
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'128' in response.data or 'długie'.encode('utf-8') in response.data.lower()

    def test_change_password_with_mismatched_passwords(self, client, test_user):
        """Test change password fails when new passwords don't match."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post('/change_password', data={
            'current_password': 'testpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'pasują'.encode('utf-8') in response.data.lower() or b'match' in response.data.lower()

    def test_change_password_with_same_as_old(self, client, test_user):
        """Test change password fails when new password equals old password."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post('/change_password', data={
            'current_password': 'testpassword123',
            'new_password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'inne' in response.data.lower() or b'different' in response.data.lower()

    def test_change_password_success(self, client, test_user, app):
        """Test successful password change."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        # Change password
        response = client.post('/change_password', data={
            'current_password': 'testpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'pomyślnie'.encode('utf-8') in response.data.lower() or b'success' in response.data.lower()

        # Verify password was actually changed in database
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            assert user.check_password('newpassword123')
            assert not user.check_password('testpassword123')

    def test_can_login_with_new_password(self, client, test_user):
        """Test that user can login with new password after change."""
        # Login with old password
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        # Change password
        client.post('/change_password', data={
            'current_password': 'testpassword123',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123'
        })

        # Logout
        client.get('/logout')

        # Try to login with old password (should fail)
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=True)
        assert 'nieprawidłowa'.encode('utf-8') in response.data.lower() or b'invalid' in response.data.lower()

        # Login with new password (should succeed)
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'newpassword123'
        }, follow_redirects=True)
        assert b'Witaj' in response.data or b'welcome' in response.data.lower()

    def test_change_password_trims_whitespace(self, client, test_user):
        """Test that password change trims leading/trailing whitespace."""
        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        # Change password with whitespace
        response = client.post('/change_password', data={
            'current_password': '  testpassword123  ',
            'new_password': '  newpassword123  ',
            'confirm_password': '  newpassword123  '
        }, follow_redirects=True)
        assert response.status_code == 200
        assert 'pomyślnie'.encode('utf-8') in response.data.lower() or b'success' in response.data.lower()

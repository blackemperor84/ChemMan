"""Tests for the can_update_databases permission.

The permission had a model column, a migration, a decorator and two admin-UI
checkboxes, but no route ever used it - every /databases route was admin-only,
so granting it silently did nothing. These tests pin the wired-up behaviour.
"""
import pytest

from models import User, db


@pytest.fixture
def db_updater(db_session, test_location):
    """A non-admin user allowed to update the CLP/SVHC reference databases."""
    user = User(username='dbupdater')
    user.set_password('updaterpass123')
    user.can_view = True
    user.can_update_databases = True
    user.organizational_unit_id = test_location.id
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def plain_user(db_session, test_location):
    """A non-admin user WITHOUT the permission."""
    user = User(username='plainuser')
    user.set_password('plainpass123')
    user.can_view = True
    user.can_update_databases = False
    user.organizational_unit_id = test_location.id
    db_session.add(user)
    db_session.commit()
    return user


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password},
                       follow_redirects=True)


class TestManageDatabasesAccess:
    def test_permitted_user_can_open_page(self, client, db_updater):
        login(client, 'dbupdater', 'updaterpass123')
        response = client.get('/admin/databases')
        assert response.status_code == 200

    def test_admin_still_has_access(self, client, admin_user):
        login(client, 'admin', 'adminpassword123')
        response = client.get('/admin/databases')
        assert response.status_code == 200

    def test_user_without_permission_is_redirected(self, client, plain_user):
        login(client, 'plainuser', 'plainpass123')
        response = client.get('/admin/databases')
        assert response.status_code == 302
        assert '/admin/databases' not in response.headers.get('Location', '')

    def test_anonymous_is_redirected_to_login(self, client):
        response = client.get('/admin/databases')
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')


class TestUploadRoutesAccess:
    @pytest.mark.parametrize('endpoint', [
        '/admin/databases/upload/clp',
        '/admin/databases/upload/svhc',
    ])
    def test_user_without_permission_cannot_post(self, client, plain_user, endpoint):
        login(client, 'plainuser', 'plainpass123')
        response = client.post(endpoint, data={}, follow_redirects=False)
        assert response.status_code == 302
        assert 'databases' not in response.headers.get('Location', '')

    @pytest.mark.parametrize('endpoint', [
        '/admin/databases/upload/clp',
        '/admin/databases/upload/svhc',
    ])
    def test_permitted_user_reaches_the_handler(self, client, db_updater, endpoint):
        """Reaching the handler (and failing on the missing file) proves it got past the guard."""
        login(client, 'dbupdater', 'updaterpass123')
        response = client.post(endpoint, data={}, follow_redirects=False)
        assert response.status_code == 302
        # The handler's own "no file" branch redirects back to the databases page;
        # the permission guard would have sent us to the index instead.
        assert 'databases' in response.headers.get('Location', '')


class TestNavigationVisibility:
    def test_link_shown_to_permitted_user(self, client, db_updater):
        response = login(client, 'dbupdater', 'updaterpass123')
        assert b'Bazy Danych' in response.data

    def test_link_hidden_from_user_without_permission(self, client, plain_user):
        response = login(client, 'plainuser', 'plainpass123')
        assert b'Bazy Danych' not in response.data

    def test_admin_only_links_stay_admin_only(self, client, db_updater):
        """The permission must not leak user management or the audit log."""
        response = login(client, 'dbupdater', 'updaterpass123')
        assert b'Zarz\xc4\x85dzaj U\xc5\xbctk.' not in response.data
        assert b'Dziennik Zmian' not in response.data

    def test_permitted_user_cannot_reach_user_management(self, client, db_updater):
        login(client, 'dbupdater', 'updaterpass123')
        response = client.get('/admin/users')
        assert response.status_code == 302

    def test_permitted_user_cannot_reach_changelog(self, client, db_updater):
        login(client, 'dbupdater', 'updaterpass123')
        response = client.get('/admin/changelog')
        assert response.status_code == 302

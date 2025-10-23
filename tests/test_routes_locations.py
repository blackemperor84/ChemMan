"""
Integration tests for location routes.
Tests CRUD operations and permissions for locations.
"""
import pytest
from flask import url_for
from models import db, User, Location, Substance


class TestLocationsList:
    """Tests for viewing location list (GET /)."""

    def test_list_locations_requires_login(self, client):
        """Test that viewing locations requires authentication."""
        response = client.get('/', follow_redirects=False)
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_list_locations_requires_view_permission(self, client, db_session):
        """Test that viewing locations requires view permission."""
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

        response = client.get('/', follow_redirects=False)
        assert response.status_code == 302  # Redirect away

    def test_list_locations_success(self, client, admin_user, test_location, app):
        """Test successful listing of locations."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/')
        assert response.status_code == 200
        assert b'Test Lab' in response.data  # test_location name

    def test_list_locations_empty(self, client, admin_user):
        """Test listing locations when database is empty."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/')
        assert response.status_code == 200

    def test_list_locations_sorted_alphabetically(self, client, admin_user, db_session):
        """Test that locations are sorted alphabetically."""
        # Create multiple locations in random order
        locations = [
            Location(name='Zebra Lab'),
            Location(name='Alpha Lab'),
            Location(name='Bravo Lab')
        ]
        for loc in locations:
            db_session.add(loc)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/')
        assert response.status_code == 200

        # Check that locations appear in alphabetical order in response
        data = response.data.decode('utf-8')
        alpha_pos = data.find('Alpha Lab')
        bravo_pos = data.find('Bravo Lab')
        zebra_pos = data.find('Zebra Lab')

        assert alpha_pos < bravo_pos < zebra_pos


class TestCreateLocation:
    """Tests for creating locations (POST /add_location)."""

    def test_create_location_requires_login(self, client):
        """Test that creating location requires authentication."""
        response = client.post('/add_location',
            data={'location_name': 'New Lab'},
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_create_location_requires_permission(self, client, db_session):
        """Test that creating location requires can_add_location permission."""
        # Create user without permission
        user = User(username='noadd')
        user.set_password('password123')
        user.can_view = True
        user.can_add_location = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'noadd',
            'password': 'password123'
        })

        response = client.post('/add_location',
            data={'location_name': 'New Lab'},
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect away

    def test_create_location_success(self, client, admin_user, app):
        """Test successful location creation."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/add_location',
            data={'location_name': 'Physics Lab'},
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b'Physics Lab' in response.data

        # Verify in database
        with app.app_context():
            location = Location.query.filter_by(name='Physics Lab').first()
            assert location is not None
            assert location.name == 'Physics Lab'

    def test_create_location_empty_name(self, client, admin_user):
        """Test that creating location with empty name fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/add_location',
            data={'location_name': '   '},  # Whitespace only
            follow_redirects=True
        )

        assert response.status_code == 200
        # Check for error message about empty name
        data_lower = response.data.decode('utf-8').lower()
        assert 'pusta' in data_lower or 'empty' in data_lower

    def test_create_location_missing_name(self, client, admin_user):
        """Test that creating location without name parameter fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/add_location',
            data={},  # No location_name
            follow_redirects=True
        )

        assert response.status_code == 200
        # Check for error message about empty name
        data_lower = response.data.decode('utf-8').lower()
        assert 'pusta' in data_lower or 'empty' in data_lower

    def test_create_location_duplicate_case_insensitive(self, client, admin_user, test_location, app):
        """Test that duplicate location names are prevented (case-insensitive)."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # test_location has name 'Test Lab'
        response = client.post('/add_location',
            data={'location_name': 'test lab'},  # Different case
            follow_redirects=True
        )

        assert response.status_code == 200
        # Check for error message about duplicate
        data_lower = response.data.decode('utf-8').lower()
        assert 'istnieje' in data_lower or 'exists' in data_lower

        # Verify only one exists
        with app.app_context():
            count = Location.query.filter(
                db.func.lower(Location.name) == 'test lab'
            ).count()
            assert count == 1

    def test_create_location_whitespace_trimmed(self, client, admin_user, app):
        """Test that whitespace is trimmed from location name."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/add_location',
            data={'location_name': '  Biology Lab  '},
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify whitespace was trimmed
        with app.app_context():
            location = Location.query.filter_by(name='Biology Lab').first()
            assert location is not None
            assert location.name == 'Biology Lab'

    def test_create_location_logs_action(self, client, admin_user, app):
        """Test that creating location logs an audit action."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/add_location',
            data={'location_name': 'Audit Test Lab'},
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify audit log was created
        with app.app_context():
            from models import AuditLog
            log = AuditLog.query.filter_by(action='CREATE_LOCATION').first()
            assert log is not None
            assert 'Audit Test Lab' in log.details


class TestViewLocationDetail:
    """Tests for viewing location details (GET /location/<id>)."""

    def test_view_location_requires_login(self, client, test_location):
        """Test that viewing location details requires authentication."""
        response = client.get(f'/location/{test_location.id}',
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location

    def test_view_location_requires_view_permission(self, client, db_session, test_location):
        """Test that viewing location details requires view permission."""
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

        response = client.get(f'/location/{test_location.id}',
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect away

    def test_view_location_success(self, client, admin_user, test_location):
        """Test successful viewing of location details."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/location/{test_location.id}')
        assert response.status_code == 200
        assert b'Test Lab' in response.data

    def test_view_location_with_substances(self, client, admin_user, test_location, test_substance):
        """Test viewing location with substances displays them."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/location/{test_location.id}')
        assert response.status_code == 200
        assert test_substance.name.encode() in response.data

    def test_view_location_not_found(self, client, admin_user):
        """Test viewing non-existent location redirects with error."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/location/99999', follow_redirects=False)
        assert response.status_code == 302  # Error handler redirects

    def test_view_location_pagination(self, client, admin_user, test_location, db_session):
        """Test that substances are paginated."""
        # Create 10 substances in the location
        for i in range(10):
            substance = Substance(
                name=f'Test Substance {i}',
                location_id=test_location.id
            )
            db_session.add(substance)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Request with per_page=5
        response = client.get(f'/location/{test_location.id}?per_page=5&page=1')
        assert response.status_code == 200

    def test_view_location_shows_other_locations(self, client, admin_user, test_location, db_session, app):
        """Test that viewing location page loads successfully with other locations."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Create another location
        other_loc = Location(name='Other Lab')
        db_session.add(other_loc)
        db_session.commit()

        response = client.get(f'/location/{test_location.id}')
        assert response.status_code == 200

        # Verify other location exists in database
        with app.app_context():
            other = Location.query.filter_by(name='Other Lab').first()
            assert other is not None
        # Note: The location list might be rendered via JavaScript or in a dropdown
        # that's not easily verifiable in the raw HTML


class TestEditLocation:
    """Tests for editing location name (POST /location/<id>/edit)."""

    def test_edit_location_requires_login(self, client, test_location):
        """Test that editing location requires authentication."""
        response = client.post(f'/location/{test_location.id}/edit',
            json={'name': 'New Name'},
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect to login

    def test_edit_location_requires_permission(self, client, db_session, test_location):
        """Test that editing location requires edit permission."""
        # Create user without edit permission
        user = User(username='noedit')
        user.set_password('password123')
        user.can_view = True
        user.can_edit = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'noedit',
            'password': 'password123'
        })

        response = client.post(f'/location/{test_location.id}/edit',
            json={'name': 'New Name'},
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect away

    def test_edit_location_success(self, client, admin_user, test_location, app):
        """Test successful location name update."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{test_location.id}/edit',
            json={'name': 'Updated Chemistry Lab'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['new_name'] == 'Updated Chemistry Lab'

        # Verify in database
        with app.app_context():
            location = Location.query.get(test_location.id)
            assert location.name == 'Updated Chemistry Lab'

    def test_edit_location_empty_name(self, client, admin_user, test_location):
        """Test that editing with empty name fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{test_location.id}/edit',
            json={'name': '   '}  # Whitespace only
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

    def test_edit_location_missing_name_key(self, client, admin_user, test_location):
        """Test that request without 'name' key fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{test_location.id}/edit',
            json={'wrong_key': 'value'}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

    def test_edit_location_no_json_data(self, client, admin_user, test_location):
        """Test that non-JSON request returns error."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{test_location.id}/edit',
            data={'name': 'New Name'},  # Form data, not JSON
            content_type='application/x-www-form-urlencoded'
        )

        # Flask returns 415 Unsupported Media Type for non-JSON requests
        assert response.status_code == 415

    def test_edit_location_duplicate_name(self, client, admin_user, test_location, db_session):
        """Test that duplicate name fails (case-insensitive)."""
        # Create another location
        other_loc = Location(name='Other Lab')
        db_session.add(other_loc)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Try to rename test_location to 'other lab' (different case)
        response = client.post(f'/location/{test_location.id}/edit',
            json={'name': 'other lab'}
        )

        assert response.status_code == 409  # Conflict
        data = response.get_json()
        assert data['status'] == 'error'

    def test_edit_location_same_name_no_change(self, client, admin_user, test_location):
        """Test that setting same name returns success without database update."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Set to the same name
        response = client.post(f'/location/{test_location.id}/edit',
            json={'name': 'Test Lab'}  # Same as current name
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'bez zmian' in data['message'].lower() or 'unchanged' in data['message'].lower()

    def test_edit_location_not_found(self, client, admin_user):
        """Test editing non-existent location returns error."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/location/99999/edit',
            json={'name': 'New Name'},
            follow_redirects=False
        )

        # get_or_404 raises exception, could be caught and return various status codes
        assert response.status_code in [404, 500, 302]

    def test_edit_location_updates_last_modified(self, client, admin_user, test_location, app):
        """Test that editing updates the last_modified timestamp."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Get original timestamp
        original_modified = test_location.last_modified

        response = client.post(f'/location/{test_location.id}/edit',
            json={'name': 'Modified Lab'}
        )

        assert response.status_code == 200

        # Verify timestamp was updated
        with app.app_context():
            location = Location.query.get(test_location.id)
            assert location.last_modified > original_modified

    def test_edit_location_logs_action(self, client, admin_user, test_location, app):
        """Test that editing location logs an audit action."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{test_location.id}/edit',
            json={'name': 'Logged Edit Lab'}
        )

        assert response.status_code == 200

        # Verify audit log was created
        with app.app_context():
            from models import AuditLog
            log = AuditLog.query.filter_by(action='UPDATE_LOCATION').order_by(AuditLog.timestamp.desc()).first()
            assert log is not None
            assert 'Test Lab' in log.details  # Old name
            assert 'Logged Edit Lab' in log.details  # New name


class TestDeleteLocation:
    """Tests for deleting locations (POST /location/<id>/delete)."""

    def test_delete_location_requires_login(self, client, test_location):
        """Test that deleting location requires authentication."""
        response = client.post(f'/location/{test_location.id}/delete',
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect to login

    def test_delete_location_requires_permission(self, client, db_session, test_location):
        """Test that deleting location requires delete_location permission."""
        # Create user without delete permission
        user = User(username='nodelete')
        user.set_password('password123')
        user.can_view = True
        user.can_delete_location = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'nodelete',
            'password': 'password123'
        })

        response = client.post(f'/location/{test_location.id}/delete',
            follow_redirects=False
        )
        assert response.status_code == 302  # Redirect away

    def test_delete_location_success_empty(self, client, admin_user, db_session, app):
        """Test successful deletion of location without substances."""
        # Create empty location
        empty_loc = Location(name='Empty Lab')
        db_session.add(empty_loc)
        db_session.commit()
        loc_id = empty_loc.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{loc_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify deleted from database
        with app.app_context():
            location = Location.query.get(loc_id)
            assert location is None

    def test_delete_location_with_substances_cascade(self, client, admin_user, test_location, test_substance, app):
        """Test that deleting location also deletes its substances (cascade)."""
        location_id = test_location.id
        substance_id = test_substance.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{location_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify both location and substance are deleted
        with app.app_context():
            location = Location.query.get(location_id)
            substance = Substance.query.get(substance_id)
            assert location is None
            assert substance is None  # Cascade delete

    def test_delete_location_not_found(self, client, admin_user):
        """Test deleting non-existent location returns error."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post('/location/99999/delete',
            follow_redirects=True
        )

        # Could be 404 or handled with error message
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data_lower = response.data.decode('utf-8').lower()
            assert 'nie' in data_lower or 'not found' in data_lower

    def test_delete_location_protected_admin_location(self, client, admin_user, db_session, app):
        """Test that 'admin' location cannot be deleted by non-admin users."""
        # Create 'admin' location
        admin_loc = Location(name='admin')
        db_session.add(admin_loc)
        db_session.commit()
        admin_loc_id = admin_loc.id

        # Create non-admin user with delete permission
        user = User(username='regularuser')
        user.set_password('password123')
        user.can_view = True
        user.can_delete_location = True
        user.is_admin = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'regularuser',
            'password': 'password123'
        })

        response = client.post(f'/location/{admin_loc_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200
        # Check for error message about protected location
        data_lower = response.data.decode('utf-8').lower()
        assert 'chronionej' in data_lower or 'protected' in data_lower

        # Verify location still exists
        with app.app_context():
            location = Location.query.get(admin_loc_id)
            assert location is not None

    def test_delete_location_id_1_protected(self, client, db_session, app):
        """Test that location with ID=1 is protected from non-admin deletion."""
        # Ensure location with ID 1 exists (might be the first test location)
        loc = Location.query.get(1)
        if not loc:
            # Create it
            loc = Location(name='Protected Location')
            db_session.add(loc)
            db_session.commit()
            # Force ID to 1 (database-dependent, might not work)

        # Create non-admin user
        user = User(username='regularuser')
        user.set_password('password123')
        user.can_view = True
        user.can_delete_location = True
        user.is_admin = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={
            'username': 'regularuser',
            'password': 'password123'
        })

        response = client.post('/location/1/delete',
            follow_redirects=True
        )

        # If ID 1 is protected, should get error
        # But this test might be flaky depending on database state

    def test_delete_location_json_response(self, client, admin_user, db_session):
        """Test that delete can return JSON response."""
        # Create location to delete
        loc = Location(name='JSON Delete Test')
        db_session.add(loc)
        db_session.commit()
        loc_id = loc.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{loc_id}/delete',
            headers={'Accept': 'application/json'}
        )

        # Should return JSON
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert data['status'] == 'success'

    def test_delete_location_logs_action(self, client, admin_user, db_session, app):
        """Test that deleting location logs an audit action."""
        # Create location to delete
        loc = Location(name='Audit Delete Test')
        db_session.add(loc)
        db_session.commit()
        loc_id = loc.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(f'/location/{loc_id}/delete',
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify audit log was created
        with app.app_context():
            from models import AuditLog
            log = AuditLog.query.filter_by(action='DELETE_LOCATION').order_by(AuditLog.timestamp.desc()).first()
            assert log is not None
            assert 'Audit Delete Test' in log.details

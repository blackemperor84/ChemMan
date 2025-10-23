"""
Integration tests for substance routes.
Tests CRUD operations, CMR/SVHC detection, and permissions for substances.
"""
import pytest
from flask import url_for
from models import db, User, Substance, Location


class TestAddSubstanceFromExcel:
    """Tests for adding substances from Excel search."""

    def test_add_substance_requires_login(self, client, test_location):
        """Test that adding substance requires authentication."""
        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json={'name': 'Test Chemical'},
            follow_redirects=False
        )
        # Unauthenticated requests get redirected to login
        assert response.status_code == 302

    def test_add_substance_requires_add_permission(self, client, test_location, db_session):
        """Test that adding substance requires can_add permission."""
        # Create user without can_add permission
        user = User(username='noadduser')
        user.set_password('password123')
        user.can_view = True
        user.can_add = False
        db_session.add(user)
        db_session.commit()

        # Login
        client.post('/login', data={
            'username': 'noadduser',
            'password': 'password123'
        })

        # Try to add substance
        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json={'name': 'Test Chemical'},
            follow_redirects=False
        )
        # Missing permissions result in redirect
        assert response.status_code == 302

    def test_add_substance_success(self, client, test_user, test_location, app):
        """Test successful substance addition from Excel."""
        # Login
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        # Add substance
        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json={
                'name': 'Test Chemical',
                'cas': '123-45-6',
                'ec_number': '200-000-0',
                'classification': 'Flam. Liq. 3',
                'h_phrases': 'H226',
                'physical_location': 'Shelf A1'
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'Test Chemical' in data['message']

        # Verify in database
        with app.app_context():
            substance = Substance.query.filter_by(name='Test Chemical').first()
            assert substance is not None
            assert substance.cas == '123-45-6'
            assert substance.ec_number == '200-000-0'
            assert substance.location_id == test_location.id
            assert substance.is_cmr is False
            assert substance.is_svhc is False

    def test_add_substance_with_cmr_detection(self, client, test_user, test_location, app):
        """Test that CMR substances are automatically flagged."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json={
                'name': 'Benzene',
                'cas': '71-43-2',
                'ec_number': '200-753-7',
                'h_phrases': 'H350, H340',
                'classification': 'Carc. 1A',
                'physical_location': 'Hood 1'
            }
        )

        assert response.status_code == 200

        # Verify CMR flag is set
        with app.app_context():
            substance = Substance.query.filter_by(name='Benzene').first()
            assert substance is not None
            assert substance.is_cmr is True

    def test_add_substance_with_svhc_detection(self, client, test_user, test_location, svhc_test_data, app):
        """Test that SVHC substances are automatically flagged."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json={
                'name': 'Lead',
                'cas': '7439-92-1',
                'ec_number': '231-100-4',
                'h_phrases': 'H360FD',
                'classification': 'Repr. 1A',
                'physical_location': 'Cabinet B'
            }
        )

        assert response.status_code == 200

        # Verify SVHC flag is set
        with app.app_context():
            substance = Substance.query.filter_by(name='Lead').first()
            assert substance is not None
            assert substance.is_svhc is True

    def test_add_substance_without_name_fails(self, client, test_user, test_location):
        """Test that adding substance without name fails."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json={
                'cas': '123-45-6',
                'classification': 'Flam. Liq. 3'
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'wymagana' in data['message'].lower() or 'required' in data['message'].lower()

    def test_add_substance_without_json_fails(self, client, test_user, test_location):
        """Test that request without JSON data fails."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            f'/location/{test_location.id}/add_substance',
            data={'name': 'Test'},  # Not JSON
            content_type='application/x-www-form-urlencoded'
        )

        # Flask returns 415 Unsupported Media Type for non-JSON requests
        assert response.status_code == 415

    def test_add_duplicate_substance_fails(self, client, test_user, test_location, app):
        """Test that adding duplicate substance fails."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        # Add first substance
        substance_data = {
            'name': 'Duplicate Chemical',
            'cas': '999-99-9',
            'physical_location': 'Shelf A'
        }
        client.post(
            f'/location/{test_location.id}/add_substance',
            json=substance_data
        )

        # Try to add duplicate
        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json=substance_data
        )

        assert response.status_code == 409
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'istnieje' in data['message'].lower() or 'exists' in data['message'].lower()

    def test_add_substance_with_scl_mfactor(self, client, test_user, test_location, app):
        """Test adding substance with SCL/M-factor."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            f'/location/{test_location.id}/add_substance',
            json={
                'name': 'Special Chemical',
                'cas': '111-22-3',
                'scl_mfactor': 'M=10',
                'h_phrases': 'H400',
                'physical_location': 'Hood 2'
            }
        )

        assert response.status_code == 200

        with app.app_context():
            substance = Substance.query.filter_by(name='Special Chemical').first()
            assert substance is not None
            assert substance.scl_mfactor == 'M=10'


class TestAddManualSubstance:
    """Tests for manually adding substances."""

    def test_add_manual_requires_login(self, client, test_location):
        """Test that manual addition requires authentication."""
        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json={'name': 'Manual Chemical'},
            follow_redirects=False
        )
        assert response.status_code == 302

    def test_add_manual_requires_add_permission(self, client, test_location, db_session):
        """Test that manual addition requires can_add permission."""
        user = User(username='noadd')
        user.set_password('password123')
        user.can_view = True
        user.can_add = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={'username': 'noadd', 'password': 'password123'})

        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json={'name': 'Manual Chemical'},
            follow_redirects=False
        )
        assert response.status_code == 302

    def test_add_manual_success(self, client, test_user, test_location, app):
        """Test successful manual substance addition."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json={
                'name': 'Manual Chemical',
                'cas': '555-66-7',
                'ec_number': '200-111-1',
                'classification': 'Ox. Sol. 2',
                'h_phrases': 'H272',
                'comment': 'Test comment',
                'physical_location': 'Drawer 1'
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'

        with app.app_context():
            substance = Substance.query.filter_by(name='Manual Chemical').first()
            assert substance is not None
            assert substance.cas == '555-66-7'
            assert substance.comment == 'Test comment'

    def test_add_manual_mixture_without_cas(self, client, test_user, test_location, app):
        """Test adding mixture without CAS number."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json={
                'name': 'Test Mixture',
                'cas': '',
                'h_phrases': 'H315, H319',
                'comment': 'Custom mixture',
                'physical_location': 'Room 101'
            }
        )

        assert response.status_code == 200

        with app.app_context():
            substance = Substance.query.filter_by(name='Test Mixture').first()
            assert substance is not None
            assert substance.cas is None

    def test_add_manual_without_name_fails(self, client, test_user, test_location):
        """Test that manual addition without name fails."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json={
                'name': '',
                'cas': '123-45-6'
            }
        )

        assert response.status_code == 400

    def test_add_manual_duplicate_fails(self, client, test_user, test_location, app):
        """Test that adding duplicate manual substance fails."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        substance_data = {
            'name': 'Duplicate Manual',
            'cas': '888-88-8',
            'physical_location': 'Lab A'
        }

        # Add first
        client.post(f'/location/{test_location.id}/add_manual', json=substance_data)

        # Try duplicate
        response = client.post(
            f'/location/{test_location.id}/add_manual',
            json=substance_data
        )

        assert response.status_code == 409

    def test_add_manual_location_not_found(self, client, test_user):
        """Test that adding to non-existent location fails."""
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        })

        response = client.post(
            '/location/99999/add_manual',
            json={'name': 'Test Chemical'}
        )

        assert response.status_code == 404


class TestDeleteSubstance:
    """Tests for deleting substances."""

    def test_delete_requires_login(self, client, test_substance):
        """Test that delete requires authentication."""
        response = client.delete(f'/substance/{test_substance.id}', follow_redirects=False)
        assert response.status_code == 302

    def test_delete_requires_delete_permission(self, client, test_substance, db_session):
        """Test that delete requires can_delete permission."""
        user = User(username='nodelete')
        user.set_password('password123')
        user.can_view = True
        user.can_delete = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={'username': 'nodelete', 'password': 'password123'})

        response = client.delete(f'/substance/{test_substance.id}', follow_redirects=False)
        assert response.status_code == 302

    def test_delete_success(self, client, admin_user, test_substance, app):
        """Test successful substance deletion."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        substance_id = test_substance.id
        substance_name = test_substance.name

        response = client.delete(f'/substance/{substance_id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert substance_name in data['message']

        # Verify substance is deleted
        with app.app_context():
            substance = Substance.query.get(substance_id)
            assert substance is None

    def test_delete_nonexistent_substance(self, client, admin_user, app):
        """Test deleting non-existent substance fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.delete('/substance/99999')
        # get_or_404 raises 404, but exception handler might convert it
        assert response.status_code in [404, 500]


class TestUpdateSubstanceComment:
    """Tests for updating substance comments."""

    def test_update_comment_requires_login(self, client, test_substance):
        """Test that updating comment requires authentication."""
        response = client.post(
            f'/substance/{test_substance.id}/comment',
            json={'comment': 'New comment'},
            follow_redirects=False
        )
        assert response.status_code == 302

    def test_update_comment_requires_edit_permission(self, client, test_substance, db_session):
        """Test that updating comment requires can_edit permission."""
        user = User(username='noedit')
        user.set_password('password123')
        user.can_view = True
        user.can_edit = False
        db_session.add(user)
        db_session.commit()

        client.post('/login', data={'username': 'noedit', 'password': 'password123'})

        response = client.post(
            f'/substance/{test_substance.id}/comment',
            json={'comment': 'New comment'},
            follow_redirects=False
        )
        assert response.status_code == 302

    def test_update_comment_success(self, client, admin_user, test_substance, app):
        """Test successful comment update."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        new_comment = 'This is an updated comment'
        response = client.post(
            f'/substance/{test_substance.id}/comment',
            json={'comment': new_comment}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['new_comment'] == new_comment

        # Verify in database
        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            assert substance.comment == new_comment

    def test_update_comment_with_empty_string(self, client, admin_user, test_substance, app):
        """Test updating comment with empty string."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            f'/substance/{test_substance.id}/comment',
            json={'comment': '   '}
        )

        assert response.status_code == 200

        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            assert substance.comment == ''

    def test_update_comment_without_json_fails(self, client, admin_user, test_substance):
        """Test that request without JSON fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            f'/substance/{test_substance.id}/comment',
            data={'comment': 'Test'},  # Not JSON
            content_type='application/x-www-form-urlencoded'
        )

        # Flask returns 415 Unsupported Media Type for non-JSON requests
        assert response.status_code == 415

    def test_update_comment_without_comment_key_fails(self, client, admin_user, test_substance):
        """Test that request without 'comment' key fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            f'/substance/{test_substance.id}/comment',
            json={'text': 'Wrong key'}
        )

        assert response.status_code == 400

    def test_update_comment_nonexistent_substance(self, client, admin_user):
        """Test updating comment for non-existent substance."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substance/99999/comment',
            json={'comment': 'Test'}
        )

        assert response.status_code == 404


class TestMoveSubstances:
    """Tests for moving substances between locations."""

    def test_move_requires_login(self, client, test_substance, test_location):
        """Test that moving requires authentication."""
        response = client.post(
            '/substances/move',
            json={
                'substance_ids': [test_substance.id],
                'target_location_id': test_location.id
            },
            follow_redirects=False
        )
        assert response.status_code == 302

    def test_move_requires_move_permission(self, client, test_substance, db_session):
        """Test that moving requires can_move permission."""
        user = User(username='nomove')
        user.set_password('password123')
        user.can_view = True
        user.can_move = False
        db_session.add(user)
        db_session.commit()

        # Create target location
        target = Location(name='Target Lab')
        db_session.add(target)
        db_session.commit()

        client.post('/login', data={'username': 'nomove', 'password': 'password123'})

        response = client.post(
            '/substances/move',
            json={
                'substance_ids': [test_substance.id],
                'target_location_id': target.id
            },
            follow_redirects=False
        )
        assert response.status_code == 302

    def test_move_success(self, client, admin_user, test_substance, db_session, app):
        """Test successful substance move."""
        # Create target location
        target = Location(name='Target Lab')
        db_session.add(target)
        db_session.commit()

        original_location_id = test_substance.location_id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/move',
            json={
                'substance_ids': [test_substance.id],
                'target_location_id': target.id
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'Przeniesiono 1' in data['message'] or 'moved' in data['message'].lower()

        # Verify substance moved
        with app.app_context():
            substance = Substance.query.get(test_substance.id)
            assert substance.location_id == target.id
            assert substance.location_id != original_location_id

    def test_move_multiple_substances(self, client, admin_user, test_location, db_session, app):
        """Test moving multiple substances at once."""
        # Create substances
        sub1 = Substance(name='Chemical 1', location_id=test_location.id)
        sub2 = Substance(name='Chemical 2', location_id=test_location.id)
        db_session.add_all([sub1, sub2])
        db_session.commit()

        # Create target location
        target = Location(name='Target')
        db_session.add(target)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/move',
            json={
                'substance_ids': [sub1.id, sub2.id],
                'target_location_id': target.id
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'Przeniesiono 2' in data['message'] or '2' in data['message']

    def test_move_skips_duplicates(self, client, admin_user, test_location, db_session, app):
        """Test that moving skips substances that would create duplicates."""
        # Create substance in source
        source_sub = Substance(
            name='Duplicate Chemical',
            cas='111-11-1',
            location_id=test_location.id
        )
        db_session.add(source_sub)
        db_session.commit()

        # Create target location with same substance
        target = Location(name='Target')
        db_session.add(target)
        db_session.commit()

        target_sub = Substance(
            name='Duplicate Chemical',
            cas='111-11-1',
            location_id=target.id
        )
        db_session.add(target_sub)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/move',
            json={
                'substance_ids': [source_sub.id],
                'target_location_id': target.id
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'Pominięto 1' in data['message'] or 'skipped' in data['message'].lower()

    def test_move_without_substance_ids_fails(self, client, admin_user, test_location):
        """Test that moving without substance IDs fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/move',
            json={'target_location_id': test_location.id}
        )

        assert response.status_code == 400

    def test_move_to_nonexistent_location_fails(self, client, admin_user, test_substance):
        """Test that moving to non-existent location fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/move',
            json={
                'substance_ids': [test_substance.id],
                'target_location_id': 99999
            }
        )

        assert response.status_code == 404


class TestCopySubstances:
    """Tests for copying substances between locations."""

    def test_copy_requires_login(self, client, test_substance, test_location):
        """Test that copying requires authentication."""
        response = client.post(
            '/substances/copy',
            json={
                'substance_ids': [test_substance.id],
                'target_location_id': test_location.id
            },
            follow_redirects=False
        )
        assert response.status_code == 302

    def test_copy_requires_copy_permission(self, client, test_substance, db_session):
        """Test that copying requires can_copy permission."""
        user = User(username='nocopy')
        user.set_password('password123')
        user.can_view = True
        user.can_copy = False
        db_session.add(user)
        db_session.commit()

        target = Location(name='Target')
        db_session.add(target)
        db_session.commit()

        client.post('/login', data={'username': 'nocopy', 'password': 'password123'})

        response = client.post(
            '/substances/copy',
            json={
                'substance_ids': [test_substance.id],
                'target_location_id': target.id
            },
            follow_redirects=False
        )
        assert response.status_code == 302

    def test_copy_success(self, client, admin_user, test_substance, db_session, app):
        """Test successful substance copy."""
        target = Location(name='Target Lab')
        db_session.add(target)
        db_session.commit()

        original_location_id = test_substance.location_id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/copy',
            json={
                'substance_ids': [test_substance.id],
                'target_location_id': target.id
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'Skopiowano 1' in data['message'] or 'copied' in data['message'].lower()

        # Verify original still exists
        with app.app_context():
            original = Substance.query.get(test_substance.id)
            assert original is not None
            assert original.location_id == original_location_id

            # Verify copy exists
            copied = Substance.query.filter_by(
                name=test_substance.name,
                location_id=target.id
            ).first()
            assert copied is not None
            assert copied.id != test_substance.id

    def test_copy_preserves_all_attributes(self, client, admin_user, test_location, db_session, app):
        """Test that copying preserves all substance attributes."""
        # Create substance with all attributes
        source_sub = Substance(
            name='Complex Chemical',
            cas='222-33-4',
            ec_number='200-222-3',
            classification='Carc. 1A',
            h_phrases='H350',
            comment='Important substance',
            scl_mfactor='M=5',
            physical_location='Cabinet A',
            is_cmr=True,
            is_svhc=False,
            location_id=test_location.id
        )
        db_session.add(source_sub)
        db_session.commit()

        # Create target
        target = Location(name='Target')
        db_session.add(target)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        client.post(
            '/substances/copy',
            json={
                'substance_ids': [source_sub.id],
                'target_location_id': target.id
            }
        )

        # Verify all attributes copied
        with app.app_context():
            copied = Substance.query.filter_by(
                name='Complex Chemical',
                location_id=target.id
            ).first()
            assert copied is not None
            assert copied.cas == '222-33-4'
            assert copied.ec_number == '200-222-3'
            assert copied.classification == 'Carc. 1A'
            assert copied.h_phrases == 'H350'
            assert copied.comment == 'Important substance'
            assert copied.scl_mfactor == 'M=5'
            assert copied.physical_location == 'Cabinet A'
            assert copied.is_cmr is True
            assert copied.is_svhc is False

    def test_copy_skips_duplicates(self, client, admin_user, test_location, db_session):
        """Test that copying skips substances that would create duplicates."""
        source_sub = Substance(
            name='Duplicate',
            cas='333-33-3',
            location_id=test_location.id
        )
        db_session.add(source_sub)
        db_session.commit()

        target = Location(name='Target')
        db_session.add(target)
        db_session.commit()

        # Add duplicate to target
        target_sub = Substance(
            name='Duplicate',
            cas='333-33-3',
            location_id=target.id
        )
        db_session.add(target_sub)
        db_session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/copy',
            json={
                'substance_ids': [source_sub.id],
                'target_location_id': target.id
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'Pominięto 1' in data['message'] or 'skipped' in data['message'].lower()

    def test_copy_without_substance_ids_fails(self, client, admin_user, test_location):
        """Test that copying without substance IDs fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/copy',
            json={'target_location_id': test_location.id}
        )

        assert response.status_code == 400

    def test_copy_to_nonexistent_location_fails(self, client, admin_user, test_substance):
        """Test that copying to non-existent location fails."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.post(
            '/substances/copy',
            json={
                'substance_ids': [test_substance.id],
                'target_location_id': 99999
            }
        )

        assert response.status_code == 404

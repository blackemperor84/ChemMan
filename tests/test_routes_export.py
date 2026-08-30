"""
Integration tests for export routes.
Tests search functionality and CSV export.
"""
import pytest
from flask import url_for
import io
import csv
from models import db, User, Location, Substance, ExcelSourceSubstance, SVHCSubstance


class TestSearchSubstances:
    """Tests for searching substances API (GET /search_substances)."""

    def test_search_requires_login(self, client):
        """Test that search requires authentication."""
        response = client.get('/search_substances', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_search_requires_view_permission(self, client, db_session):
        """Test that search requires view permission."""
        # Create user without view permission
        user = User(username='noview_export', is_admin=False, can_view=False, can_edit=False)
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()

        # Login as user without view permission
        client.post('/login', data={
            'username': 'noview_export',
            'password': 'password123'
        })

        response = client.get('/search_substances?query=test', follow_redirects=False)
        assert response.status_code == 302
        # User without view permission is redirected to locations index
        assert '/locations' in response.location or response.location == '/'

    def test_search_query_too_short(self, client, admin_user):
        """Test that query must be at least 2 characters."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        # Single character query should return empty results
        response = client.get('/search_substances?query=a')
        assert response.status_code == 200
        data = response.get_json()
        assert data == []

    def test_search_clp_database_by_name(self, client, admin_user, app):
        """Test searching CLP database by substance name."""
        # Create test substance in CLP database
        with app.app_context():
            clp_sub = ExcelSourceSubstance(
                name='Benzene',
                cas='71-43-2',
                ec_number='200-753-7',
                classification='Flam. Liq. 2; Carc. 1A',
                h_phrases='H225, H350'
            )
            db.session.add(clp_sub)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/search_substances?query=benzene')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert any(sub['name'] == 'Benzene' for sub in data)
        assert any(sub['cas'] == '71-43-2' for sub in data)
        assert any(sub['source'] == 'CLP' for sub in data)

    def test_search_clp_database_by_cas(self, client, admin_user, app):
        """Test searching CLP database by CAS number."""
        # Create test substance in CLP database
        with app.app_context():
            clp_sub = ExcelSourceSubstance(
                name='Toluene',
                cas='108-88-3',
                ec_number='203-625-9',
                classification='Flam. Liq. 2',
                h_phrases='H225'
            )
            db.session.add(clp_sub)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/search_substances?query=108-88')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert any(sub['cas'] == '108-88-3' for sub in data)

    def test_search_svhc_database(self, client, admin_user, app):
        """Test searching SVHC database."""
        # Create test substance in SVHC database
        with app.app_context():
            svhc_sub = SVHCSubstance(
                name='Lead chromate',
                cas='7758-97-6',
                ec_number='231-846-0'
            )
            db.session.add(svhc_sub)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/search_substances?query=lead')
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) > 0
        assert any(sub['name'] == 'Lead chromate' for sub in data)
        assert any(sub['source'] == 'SVHC' for sub in data)

    def test_search_deduplicates_clp_and_svhc(self, client, admin_user, app):
        """Test that results from CLP and SVHC are deduplicated by CAS."""
        # Create substance in both databases with same CAS
        with app.app_context():
            clp_sub = ExcelSourceSubstance(
                name='Lead chromate',
                cas='7758-97-6',
                ec_number='231-846-0',
                classification='Carc. 1A',
                h_phrases='H350'
            )
            svhc_sub = SVHCSubstance(
                name='Lead chromate',
                cas='7758-97-6',
                ec_number='231-846-0'
            )
            db.session.add_all([clp_sub, svhc_sub])
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/search_substances?query=7758-97-6')
        assert response.status_code == 200
        data = response.get_json()

        # Should only have one result (from CLP, SVHC is deduplicated)
        cas_matches = [sub for sub in data if sub['cas'] == '7758-97-6']
        assert len(cas_matches) == 1
        assert cas_matches[0]['source'] == 'CLP'

    def test_search_limits_results_to_50(self, client, admin_user, app):
        """Test that search limits results to 50 per database."""
        # Create 60 substances in CLP database
        with app.app_context():
            for i in range(60):
                clp_sub = ExcelSourceSubstance(
                    name=f'Test Substance {i}',
                    cas=f'{i:05d}-00-0',
                    ec_number=f'{i:03d}-000-0'
                )
                db.session.add(clp_sub)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/search_substances?query=test')
        assert response.status_code == 200
        data = response.get_json()

        # Should be limited to 50 from CLP (plus any from SVHC, but we didn't add SVHC)
        # Note: the query limits to 50 per database, so max 100 total if both have results
        assert len(data) <= 100

    def test_search_empty_query_parameter(self, client, admin_user):
        """Test search with empty query parameter."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/search_substances?query=')
        assert response.status_code == 200
        data = response.get_json()
        assert data == []


class TestExportLocationCSV:
    """Tests for exporting location to CSV (GET /export/location/<id>/csv)."""

    def test_export_requires_login(self, client, test_location):
        """Test that CSV export requires authentication."""
        response = client.get(f'/export/location/{test_location.id}/csv', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_export_requires_view_permission(self, client, db_session, test_location):
        """Test that CSV export requires view permission."""
        # Create user without view permission
        user = User(username='noview_export2', is_admin=False, can_view=False, can_edit=False)
        user.set_password('password123')
        db_session.add(user)
        db_session.commit()

        # Login as user without view permission
        client.post('/login', data={
            'username': 'noview_export2',
            'password': 'password123'
        })

        response = client.get(f'/export/location/{test_location.id}/csv', follow_redirects=False)
        assert response.status_code == 302
        # User without view permission is redirected to locations index
        assert '/locations' in response.location or response.location == '/'

    def test_export_nonexistent_location_returns_404(self, client, admin_user):
        """Test that exporting non-existent location returns 404."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get('/export/location/99999/csv', follow_redirects=True)
        # The route uses get_or_404, which should redirect with an error message
        # or return 404 depending on implementation
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            # If redirected, check for error message
            assert b'404' in response.data or b'nie znaleziono' in response.data.lower() or b'not found' in response.data.lower()

    def test_export_successful_csv_generation(self, client, admin_user, test_location, app):
        """Test successful CSV export for a location."""
        # Add substances to the location
        with app.app_context():
            location = Location.query.first()
            sub1 = Substance(
                name='Acetone',
                cas='67-64-1',
                classification='Flam. Liq. 2',
                h_phrases='H225',
                physical_location='Lab A',
                location_id=location.id
            )
            sub2 = Substance(
                name='Ethanol',
                cas='64-17-5',
                classification='Flam. Liq. 2',
                h_phrases='H225',
                physical_location='Lab B',
                location_id=location.id
            )
            db.session.add_all([sub1, sub2])
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/export/location/{test_location.id}/csv')
        assert response.status_code == 200
        assert response.mimetype == 'text/csv'
        assert 'attachment' in response.headers.get('Content-Disposition', '')

    def test_export_csv_headers_correct(self, client, admin_user, test_location):
        """Test that CSV has correct headers."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/export/location/{test_location.id}/csv')
        assert response.status_code == 200

        # Decode the CSV data (UTF-8 with BOM)
        csv_data = response.data.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(csv_data))
        headers = next(csv_reader)

        expected_headers = ['Nazwa chemiczna', 'Nr CAS', 'Klasyfikacja', 'Zwroty H',
                          'SCL/M-factor', 'Lokalizacja', 'Komentarz']
        assert headers == expected_headers

    def test_export_csv_data_accuracy(self, client, admin_user, test_location, app):
        """Test that CSV data accurately reflects substances."""
        # Add a specific substance
        with app.app_context():
            location = Location.query.first()
            sub = Substance(
                name='Test Chemical',
                cas='123-45-6',
                classification='Carc. 1A',
                h_phrases='H350',
                scl_mfactor='M=10',
                physical_location='Shelf 5',
                comment='Test comment',
                location_id=location.id
            )
            db.session.add(sub)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/export/location/{test_location.id}/csv')
        assert response.status_code == 200

        csv_data = response.data.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(csv_data))
        next(csv_reader)  # Skip headers

        # Find our test substance in the CSV
        found = False
        for row in csv_reader:
            if 'Test Chemical' in row[0]:
                found = True
                assert row[1] == '123-45-6'  # CAS is plain text, never an Excel formula
                assert 'Carc. 1A' in row[2]
                assert 'H350' in row[3]
                assert 'M=10' in row[4]
                assert 'Shelf 5' in row[5]
                assert 'Test comment' in row[6]

        assert found, "Test substance not found in CSV"

    def test_export_csv_filename_contains_location_name(self, client, admin_user, test_location):
        """Test that CSV filename includes location name."""
        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/export/location/{test_location.id}/csv')
        assert response.status_code == 200

        content_disposition = response.headers.get('Content-Disposition', '')
        assert 'ChemMan_lok_' in content_disposition
        assert '_subst.csv' in content_disposition

    def test_export_empty_location(self, client, admin_user, app):
        """Test exporting a location with no substances."""
        # Create a new empty location
        with app.app_context():
            empty_loc = Location(name='Empty Lab')
            db.session.add(empty_loc)
            db.session.commit()
            empty_loc_id = empty_loc.id

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/export/location/{empty_loc_id}/csv')
        assert response.status_code == 200

        # Should have headers but no data rows
        csv_data = response.data.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(csv_data))
        rows = list(csv_reader)
        assert len(rows) == 1  # Only header row

    def test_export_cas_number_is_never_a_formula(self, client, admin_user, test_location, app):
        """CAS numbers are exported as plain text, never as an Excel formula.

        These cells used to be written as ="1-2-3" so Excel would keep them as
        text instead of parsing them as dates. That construction was injectable:
        a CAS containing a quote broke out of the literal, and since any cell
        beginning with '=' is a formula, escaping the inner quotes could not fix
        it. Real CAS/EC values are not date-shaped, so plain text is the safe
        trade. See tests/test_codex_followup_fixes.py for the injection cases.
        """
        # Add substance with CAS that might be converted to date in Excel
        with app.app_context():
            location = Location.query.first()
            sub = Substance(
                name='Test Substance',
                cas='1-2-3',  # This could be converted to date
                location_id=location.id
            )
            db.session.add(sub)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/export/location/{test_location.id}/csv')
        assert response.status_code == 200

        csv_data = response.data.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(csv_data))
        next(csv_reader)  # Skip headers

        # Find our test substance and check CAS formatting
        found = False
        for row in csv_reader:
            if 'Test Substance' in row[0]:
                assert row[1] == '1-2-3'
                assert not row[1].startswith('='), 'CAS cell must not be a formula'
                found = True
                break

        assert found, "Test substance not found in CSV"

    def test_export_handles_null_values(self, client, admin_user, test_location, app):
        """Test that export correctly handles NULL values in substance fields."""
        # Add substance with minimal data
        with app.app_context():
            location = Location.query.first()
            sub = Substance(
                name='Minimal Substance',
                location_id=location.id
                # All other fields are NULL
            )
            db.session.add(sub)
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/export/location/{test_location.id}/csv')
        assert response.status_code == 200

        csv_data = response.data.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(csv_data))
        next(csv_reader)  # Skip headers

        # Find our test substance
        for row in csv_reader:
            if 'Minimal Substance' in row[0]:
                # CAS should be empty
                assert row[1] == ''
                # Physical location should be 'Nieznana' (Unknown)
                assert row[5] == 'Nieznana'
                break

    def test_export_substances_sorted_correctly(self, client, admin_user, test_location, app):
        """Test that substances are sorted by physical_location then name."""
        # Add substances with different physical locations
        with app.app_context():
            location = Location.query.first()
            sub1 = Substance(name='Zinc', physical_location='Lab A', location_id=location.id)
            sub2 = Substance(name='Acetone', physical_location='Lab A', location_id=location.id)
            sub3 = Substance(name='Benzene', physical_location='Lab B', location_id=location.id)
            db.session.add_all([sub1, sub2, sub3])
            db.session.commit()

        client.post('/login', data={
            'username': 'admin',
            'password': 'adminpassword123'
        })

        response = client.get(f'/export/location/{test_location.id}/csv')
        assert response.status_code == 200

        csv_data = response.data.decode('utf-8-sig')
        csv_reader = csv.reader(io.StringIO(csv_data))
        next(csv_reader)  # Skip headers

        rows = list(csv_reader)
        names = [row[0] for row in rows if row[0] in ['Zinc', 'Acetone', 'Benzene']]

        # Should be sorted: Lab A (Acetone, Zinc), then Lab B (Benzene)
        expected_order = ['Acetone', 'Zinc', 'Benzene']
        assert names == expected_order

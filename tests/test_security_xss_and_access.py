"""
Negative security tests: stored XSS and cross-unit access control.

Uzupełnia istniejące testy scenariuszy pozytywnych o przypadki, w których
użytkownik celowo próbuje obejść zabezpieczenia.
"""
import io
import json

import pytest
from markupsafe import Markup

from models import db, User, Location, Substance, SDSFile
from utils import nl2br


XSS_PAYLOAD = '<script>alert(1)</script>'
XSS_ESCAPED = '&lt;script&gt;alert(1)&lt;/script&gt;'


def make_pdf():
    """Minimalny plik z poprawnym magic number PDF."""
    return io.BytesIO(b'%PDF-1.4\n' + b'A' * 1024)


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password})


@pytest.fixture(scope='function')
def other_location(db_session):
    """Druga komórka organizacyjna - obca dla test_user."""
    location = Location(name='Other Lab')
    db_session.add(location)
    db_session.commit()
    return location


@pytest.fixture(scope='function')
def other_substance(db_session, other_location):
    """Substancja należąca do obcej komórki organizacyjnej."""
    substance = Substance(
        name='Foreign Chemical',
        cas='999-99-9',
        classification='Flam. Liq. 3',
        h_phrases='H226',
        location_id=other_location.id
    )
    db_session.add(substance)
    db_session.commit()
    return substance


class TestNl2brFilter:
    """Testy jednostkowe filtra nl2br (zastępuje replace(...)|safe)."""

    def test_escapes_html(self):
        assert '<script>' not in nl2br(XSS_PAYLOAD)
        assert XSS_ESCAPED == str(nl2br(XSS_PAYLOAD))

    def test_escapes_attribute_breakout(self):
        result = str(nl2br('" onmouseover="alert(1)'))
        assert 'onmouseover="alert(1)"' not in result
        assert '&#34;' in result or '&quot;' in result

    def test_newline_becomes_br(self):
        assert str(nl2br('H226\nH315')) == 'H226<br>H315'

    def test_custom_separator_is_not_escaped(self):
        result = str(nl2br('a\nb', "<span class='name-spacer'></span>"))
        assert result == "a<span class='name-spacer'></span>b"

    def test_escapes_each_line_separately(self):
        result = str(nl2br(f'{XSS_PAYLOAD}\n{XSS_PAYLOAD}'))
        assert result == f'{XSS_ESCAPED}<br>{XSS_ESCAPED}'

    def test_none_returns_empty(self):
        assert str(nl2br(None)) == ''

    def test_returns_markup(self):
        assert isinstance(nl2br('x'), Markup)

    def test_non_string_input(self):
        assert str(nl2br(42)) == '42'


class TestStoredXSS:
    """Zapisany HTML nie może zostać wykonany u innego użytkownika."""

    @pytest.fixture(scope='function')
    def xss_substance(self, db_session, test_location):
        substance = Substance(
            name=f'Evil {XSS_PAYLOAD}',
            cas='111-11-1',
            classification=f'Carc. 1A {XSS_PAYLOAD}',
            h_phrases=f'H350 {XSS_PAYLOAD}',
            scl_mfactor=f'M=10 {XSS_PAYLOAD}',
            location_id=test_location.id
        )
        db_session.add(substance)
        db_session.commit()
        return substance

    def test_location_detail_escapes_payload(self, client, admin_user, xss_substance, test_location):
        login(client, 'admin', 'adminpassword123')
        response = client.get(f'/location/{test_location.id}')

        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert XSS_PAYLOAD not in body
        assert XSS_ESCAPED in body

    def test_all_substances_escapes_payload(self, client, admin_user, xss_substance):
        login(client, 'admin', 'adminpassword123')
        response = client.get('/substances/all')

        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert XSS_PAYLOAD not in body
        assert XSS_ESCAPED in body

    def test_newlines_still_render_as_br(self, client, admin_user, db_session, test_location):
        """Regresja: podział na linie musi nadal działać po naprawie XSS."""
        substance = Substance(
            name='Multi Line',
            cas='222-22-2',
            h_phrases='H226\nH315',
            location_id=test_location.id
        )
        db_session.add(substance)
        db_session.commit()

        login(client, 'admin', 'adminpassword123')
        response = client.get(f'/location/{test_location.id}')

        assert 'H226<br>H315' in response.get_data(as_text=True)


class TestSDSCrossUnitAccess:
    """Uprawnienie can_upload_sds nie może dawać dostępu do cudzej komórki."""

    def test_upload_to_foreign_unit_is_rejected(self, client, test_user, other_substance, app):
        login(client, 'testuser', 'testpassword123')

        response = client.post(
            f'/substance/{other_substance.id}/upload_sds',
            data={'sds_file': (make_pdf(), 'evil.pdf')},
            content_type='multipart/form-data',
            follow_redirects=False
        )

        assert response.status_code == 302
        with app.app_context():
            substance = db.session.get(Substance, other_substance.id)
            assert substance.sds_filename is None
            assert SDSFile.query.filter_by(substance_id=other_substance.id).count() == 0

    def test_delete_from_foreign_unit_is_rejected(self, client, test_user, other_substance, db_session, app):
        sds = SDSFile(
            substance_id=other_substance.id,
            filename='foreign.pdf',
            original_filename='foreign.pdf'
        )
        db_session.add(sds)
        db_session.commit()
        sds_id = sds.id

        login(client, 'testuser', 'testpassword123')
        response = client.post(
            f'/substance/{other_substance.id}/delete_sds/{sds_id}',
            follow_redirects=False
        )

        assert response.status_code == 302
        with app.app_context():
            assert db.session.get(SDSFile, sds_id) is not None

    def test_upload_to_own_unit_still_works(self, client, test_user, test_substance, app):
        """Regresja: właściciel komórki nadal może dodać SDS."""
        login(client, 'testuser', 'testpassword123')

        response = client.post(
            f'/substance/{test_substance.id}/upload_sds',
            data={'sds_file': (make_pdf(), 'ok.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200
        with app.app_context():
            substance = db.session.get(Substance, test_substance.id)
            assert substance.sds_filename is not None

    def test_admin_can_upload_anywhere(self, client, admin_user, other_substance, app):
        login(client, 'admin', 'adminpassword123')

        response = client.post(
            f'/substance/{other_substance.id}/upload_sds',
            data={'sds_file': (make_pdf(), 'admin.pdf')},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        assert response.status_code == 200
        with app.app_context():
            substance = db.session.get(Substance, other_substance.id)
            assert substance.sds_filename is not None


class TestMoveSourceUnitAccess:
    """Przenoszenie musi weryfikować komórkę ŹRÓDŁOWĄ, nie tylko docelową."""

    def test_cannot_pull_substance_out_of_foreign_unit(self, client, test_user, other_substance, test_location, app):
        login(client, 'testuser', 'testpassword123')

        response = client.post(
            '/substances/move',
            data=json.dumps({
                'substance_ids': [other_substance.id],
                'target_location_id': test_location.id
            }),
            content_type='application/json'
        )

        assert response.status_code == 403
        with app.app_context():
            substance = db.session.get(Substance, other_substance.id)
            assert substance.location_id == other_substance.location_id

    def test_mixed_batch_is_rejected_entirely(self, client, test_user, test_substance,
                                              other_substance, test_location, app):
        """Jedna obca substancja w partii blokuje całą operację."""
        original_location_id = test_substance.location_id

        login(client, 'testuser', 'testpassword123')
        response = client.post(
            '/substances/move',
            data=json.dumps({
                'substance_ids': [test_substance.id, other_substance.id],
                'target_location_id': test_location.id
            }),
            content_type='application/json'
        )

        assert response.status_code == 403
        with app.app_context():
            assert db.session.get(Substance, test_substance.id).location_id == original_location_id
            assert db.session.get(Substance, other_substance.id).location_id == other_substance.location_id

    def test_move_within_own_unit_still_works(self, client, db_session, test_location, test_substance, app):
        """Regresja: admin (lub właściciel obu komórek) nadal może przenosić."""
        second = Location(name='Second Lab')
        db_session.add(second)
        db_session.commit()

        user = User(username='mover')
        user.set_password('moverpassword123')
        user.is_admin = True
        user.can_view = True
        user.can_move = True
        db_session.add(user)
        db_session.commit()

        login(client, 'mover', 'moverpassword123')
        response = client.post(
            '/substances/move',
            data=json.dumps({
                'substance_ids': [test_substance.id],
                'target_location_id': second.id
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        with app.app_context():
            assert db.session.get(Substance, test_substance.id).location_id == second.id

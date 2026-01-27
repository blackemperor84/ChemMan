"""
Pytest configuration and fixtures for ChemMan tests.
"""
import pytest
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, User, Location, Substance, SVHCSubstance, ExcelSourceSubstance
from config import TestingConfig
from limiter import limiter


@pytest.fixture(scope='session', autouse=True)
def disable_limiter():
    """Disable rate limiting for all tests."""
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(scope='session')
def app():
    """
    Create and configure a Flask application for testing.

    Yields:
        Flask: Configured test application
    """
    app = create_app(TestingConfig)

    # Disable rate limiting for tests
    app.config['RATELIMIT_ENABLED'] = False

    # Establish application context
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """
    Create a test client for the app.

    Args:
        app: The Flask application fixture

    Returns:
        FlaskClient: Test client for making requests
    """
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """
    Create a new database session for a test.
    Rolls back changes after each test.

    Args:
        app: The Flask application fixture

    Yields:
        SQLAlchemy Session: Database session
    """
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def test_user(db_session, test_location):
    """
    Create a test user with standard permissions assigned to test location.

    Args:
        db_session: Database session fixture
        test_location: Test location fixture

    Returns:
        User: Test user object
    """
    user = User(username='testuser')
    user.set_password('testpassword123')
    user.can_view = True
    user.can_add = True
    user.can_edit = True
    user.can_delete = True
    user.can_move = True
    user.can_copy = True
    user.can_upload_sds = True
    user.organizational_unit_id = test_location.id
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope='function')
def admin_user(db_session):
    """
    Create an admin test user with all permissions.

    Args:
        db_session: Database session fixture

    Returns:
        User: Admin test user object
    """
    admin = User(username='admin')
    admin.set_password('adminpassword123')
    admin.is_admin = True
    admin.can_view = True
    admin.can_add = True
    admin.can_edit = True
    admin.can_delete = True
    admin.can_move = True
    admin.can_copy = True
    admin.can_upload_sds = True
    admin.can_add_location = True
    admin.can_delete_location = True
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture(scope='function')
def test_location(db_session):
    """
    Create a test location.

    Args:
        db_session: Database session fixture

    Returns:
        Location: Test location object
    """
    location = Location(name='Test Lab')
    db_session.add(location)
    db_session.commit()
    return location


@pytest.fixture(scope='function')
def test_substance(db_session, test_location):
    """
    Create a test substance (non-CMR, non-SVHC).

    Args:
        db_session: Database session fixture
        test_location: Test location fixture

    Returns:
        Substance: Test substance object
    """
    substance = Substance(
        name='Test Chemical',
        cas='123-45-6',
        ec_number='200-000-0',
        classification='Flam. Liq. 3',
        h_phrases='H226',
        is_cmr=False,
        is_svhc=False,
        location_id=test_location.id
    )
    db_session.add(substance)
    db_session.commit()
    return substance


@pytest.fixture(scope='function')
def cmr_substance(db_session, test_location):
    """
    Create a test CMR substance with H350 (carcinogenic).

    Args:
        db_session: Database session fixture
        test_location: Test location fixture

    Returns:
        Substance: CMR test substance object
    """
    substance = Substance(
        name='Benzene',
        cas='71-43-2',
        ec_number='200-753-7',
        classification='Carc. 1A; Muta. 1B',
        h_phrases='H350, H340',  # Carcinogenic and mutagenic
        is_cmr=True,
        is_svhc=False,
        location_id=test_location.id
    )
    db_session.add(substance)
    db_session.commit()
    return substance


@pytest.fixture(scope='function')
def svhc_test_data(db_session):
    """
    Populate test SVHC database with sample data.

    Args:
        db_session: Database session fixture

    Returns:
        list: List of created SVHC substances
    """
    svhc_substances = [
        SVHCSubstance(
            name='Lead',
            cas='7439-92-1',
            ec_number='231-100-4',
            reason='Toxic for reproduction (Article 57c)',
            date_inclusion='2010-12-15'
        ),
        SVHCSubstance(
            name='Anthracene',
            cas='120-12-7',
            ec_number='204-371-1',
            reason='PBT (Article 57d)',
            date_inclusion='2008-10-28'
        ),
    ]

    for svhc in svhc_substances:
        db_session.add(svhc)

    db_session.commit()
    return svhc_substances

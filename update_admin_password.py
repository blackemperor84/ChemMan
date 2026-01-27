"""
Script to update the admin password using the password from .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from models import db, User

# Create app with configuration
app = create_app()

with app.app_context():
    # Get admin password from environment
    admin_password = os.environ.get('CHEM_MAN_ADMIN_PASSWORD', 'admin')

    # Find admin user
    admin_user = User.query.filter_by(username='admin').first()

    if admin_user:
        # Update password
        admin_user.set_password(admin_password)
        db.session.commit()
        print(f"SUCCESS: Admin password has been updated to the one from .env file")
        print(f"  Username: admin")
        print(f"  Password: {admin_password}")
    else:
        print("ERROR: Admin user not found in database!")
        print("  You may need to run 'flask init-db' first to create the admin user")

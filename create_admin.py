"""Create admin user if it doesn't exist"""
import os
from app import create_app
from models import db, User
from config import DevelopmentConfig

app = create_app(DevelopmentConfig)

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()

    if admin:
        print("Admin user already exists")
    else:
        print("Creating admin user...")
        # Get default password from env or use default
        default_pass = os.getenv('DEFAULT_PASSWORD', 'F23pADFE!')

        # Create admin user
        admin = User(
            username='admin',
            is_admin=True,
            can_view=True,
            can_add=True,
            can_edit=True,
            can_delete=True,
            can_move=True,
            can_copy=True,
            can_upload_sds=True,
            can_add_location=True,
            can_delete_location=True
        )
        admin.set_password(default_pass)

        db.session.add(admin)
        db.session.commit()

        print(f"Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: {default_pass}")

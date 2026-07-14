"""
Auth Service — Default admin creation and auth helpers.
"""
from extensions import db
from models import User


def create_default_admin(app):
    """Create default admin user if none exists."""
    with app.app_context():
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username=app.config.get('DEFAULT_ADMIN_USERNAME', 'admin'),
                email=app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@edutrackpro.com'),
                role='admin',
                is_active=True,
            )
            admin.set_password(app.config.get('DEFAULT_ADMIN_PASSWORD', 'Admin@123'))
            db.session.add(admin)
            db.session.commit()
            print(f'[SUCCESS] Admin user created: {admin.username}')
        else:
            print('[INFO] Admin user already exists.')

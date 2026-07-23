"""
EduTrack Pro — Application Factory
Creates and configures the Flask application.
"""
import os
import click
from datetime import datetime
from flask import Flask, render_template

from config import config
from extensions import db, login_manager, csrf, mail, jwt, migrate, limiter


def create_app(config_name: str = None) -> Flask:
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure upload directories exist
    _ensure_directories(app)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Register CLI commands
    _register_cli_commands(app)

    # Register context processors
    _register_context_processors(app)

    # Auto-initialize database tables for serverless/first-run deployments
    with app.app_context():
        try:
            db.create_all()
            from services.auth_service import create_default_admin
            create_default_admin(app)
        except Exception as e:
            app.logger.warning(f"DB auto-init notice: {e}")

    return app



def _ensure_directories(app: Flask):
    """Create required directories if they don't exist (handles read-only filesystems)."""
    dirs = [
        app.config['UPLOAD_FOLDER'],
        os.path.join(app.config['UPLOAD_FOLDER'], 'photos'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'documents'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'certificates'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'),
    ]
    for d in dirs:
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            # Serverless environments (like Vercel) have a read-only filesystem
            pass



def _register_blueprints(app: Flask):
    """Register all Flask blueprints."""
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.students import students_bp
    from routes.attendance import attendance_bp
    from routes.marks import marks_bp
    from routes.reports import reports_bp
    from routes.notifications import notifications_bp
    from routes.files import files_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(marks_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(api_bp)


def _register_error_handlers(app: Flask):
    """Register HTTP error handlers."""
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template('errors/429.html'), 429


def _register_context_processors(app: Flask):
    """Register Jinja2 context processors."""
    from models import Notification
    from flask_login import current_user

    @app.context_processor
    def inject_globals():
        unread_count = 0
        try:
            if current_user.is_authenticated:
                unread_count = Notification.query.filter_by(
                    user_id=current_user.id, is_read=False
                ).count()
        except Exception:
            unread_count = 0
        return {
            'app_name': app.config.get('APP_NAME', 'EduTrack Pro'),
            'app_version': app.config.get('APP_VERSION', '1.0.0'),
            'current_year': datetime.utcnow().year,
            'unread_notifications': unread_count,
        }



def _register_cli_commands(app: Flask):
    """Register Flask CLI commands."""

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database tables."""
        db.create_all()
        click.echo('[SUCCESS] Database tables created.')

    @app.cli.command('seed-data')
    def seed_data():
        """Seed the database with sample data."""
        from services.auth_service import create_default_admin
        from services.student_service import seed_sample_data

        create_default_admin(app)
        seed_sample_data()
        click.echo('[SUCCESS] Sample data seeded successfully.')

    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('email')
    @click.argument('password')
    def create_admin(username, email, password):
        """Create an admin user."""
        from models import User
        user = User(username=username, email=email, role='admin')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'[SUCCESS] Admin user "{username}" created.')

    @app.cli.command('reset-db')
    @click.confirmation_option(prompt='[WARNING] This will drop all tables. Are you sure?')
    def reset_db():
        """Drop and recreate all tables."""
        db.drop_all()
        db.create_all()
        click.echo('[SUCCESS] Database reset complete.')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'edutrack-pro-secret-key-change-in-production')
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf-secret-key-change-in-production')

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@edutrackpro.com')

    # File Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

    # Pagination
    STUDENTS_PER_PAGE = 15
    RECORDS_PER_PAGE = 20

    # Attendance threshold
    LOW_ATTENDANCE_THRESHOLD = 75.0

    # Admin defaults
    DEFAULT_ADMIN_USERNAME = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_EMAIL = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@edutrackpro.com')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'Admin@123')

    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"

    # App info
    APP_NAME = 'EduTrack Pro'
    APP_VERSION = '1.0.0'

    # Cloudinary (cloud file storage)
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "edutrack.db")}'
    )
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://'
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}

import os
from dotenv import load_dotenv

load_dotenv()

# Flask Configuration
DEBUG = os.getenv('FLASK_DEBUG', False)
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

# MySQL Configuration
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DB = os.getenv('MYSQL_DB', 'carbon_tracker')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24
JWT_REFRESH_EXPIRY_DAYS = 7

# AI APIs
CLARIFAI_PAT = os.getenv('CLARIFAI_PAT', '')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')

# Google Maps API
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

# TomTom Maps API
TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY', '')

# Email Configuration (for alerts)
MAIL_SERVER = os.getenv('MAIL_SERVER', '')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')

# Rate Limiting
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', True)
LOGIN_RATE_LIMIT = os.getenv('LOGIN_RATE_LIMIT', '5 per hour')
API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100 per hour')
from .base import *

# Debug should be True in development
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Cache configuration
CACHES = {
    "default": {        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get('REDIS_URL', 'redis://redis:16379/0'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 1000,
            "CONNECTION_POOL_CLASS": "redis.connection.BlockingConnectionPool",
            "IGNORE_EXCEPTIONS": True,
        }
    }
}

# Cache timeout settings
CACHE_TTL = 60 * 15  # 15 minutes default
CACHE_MIDDLEWARE_SECONDS = CACHE_TTL
CACHE_MIDDLEWARE_KEY_PREFIX = 'taskmanager_dev'

# Rate limiting with Redis
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_ENABLE = True

# Disable security settings that might interfere with local development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'taskmanager'),
        'USER': os.environ.get('POSTGRES_USER', 'taskuser'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'Admin255255@@'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,  # 1 minute connection persistence
    }
}

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Channel Layer for WebSocket
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379/0')],
        },
    },
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# WhiteNoise configuration
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # Add after SecurityMiddleware
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Authentication settings
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Django AllAuth settings
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Disable email verification in development
ACCOUNT_LOGIN_METHODS = {'email', 'username'}  # Update to new setting format
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']  # Required fields
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/5m',  # 5 failed attempts per 5 minutes
    'signup': '10/d',        # 10 signups per day
    'password_reset': '5/15m' # 5 attempts per 15 minutes
}

# Development-specific apps
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Django Debug Toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
]

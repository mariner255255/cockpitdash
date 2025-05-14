"""
Local development settings for taskmanager project.
Extends from development settings with local-specific overrides.
"""

from .development import *
from pathlib import Path

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'accounts.apps.AccountsConfig',
    'tasks.apps.TasksConfig',
]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Debug settings - Force enable for development
DEBUG = True
TEMPLATE_DEBUG = True

# Override allowed hosts for development
ALLOWED_HOSTS = ['*']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
            ],
            'debug': DEBUG,
        },
    },
]

# MIDDLEWARE configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # allauth middleware
]

# Security Middleware settings for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Django AllAuth settings
SITE_ID = 1
ACCOUNT_LOGIN_METHODS = {'username', 'email'}  # Modern django-allauth setting
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_PASSWORD_MIN_LENGTH = 12
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Disable email verification for local development
ACCOUNT_EMAIL_REQUIRED = True  # Will be inferred from ACCOUNT_SIGNUP_FIELDS but kept for clarity

# Django AllAuth Rate Limiting Settings
ACCOUNT_RATE_LIMITS = {
    'login_attempt': '5/5m',  # 5 attempts per 5 minutes
    'login_failed': '5/5m',   # 5 failed attempts per 5 minutes
    'signup': '10/d',         # 10 signups per day
    'password_reset': '5/15m' # 5 attempts per 15 minutes
}

# Rate limiting configuration
ACCOUNT_RATE_LIMITS = {
    'login_attempt': '5/5m',  # 5 attempts per 5 minutes
    'login_failed': '5/5m',   # 5 failed attempts per 5 minutes
    'signup': '10/d',         # 10 signups per day
    'password_reset': '5/15m' # 5 attempts per 15 minutes
}

# Custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# Message settings
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

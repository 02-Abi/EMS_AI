import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Email settings for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# ==================== APPLICATION DEFINITION ====================

INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # For intcomma filter in templates
    'ml_engine',
    
    # Custom apps
    'accounts',
    'employees',
    'performance',
    'audit',
]

MIDDLEWARE = [
    # Django built-in middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'employees.middleware.NoCacheMiddleware',
    # Custom middleware
    'audit.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'ems.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ems.wsgi.application'


# ==================== DATABASE CONFIGURATION ====================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ==================== AUTHENTICATION CONFIGURATION ====================

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==================== LOGIN URLS ====================

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'


# ==================== SESSION SECURITY SETTINGS ====================
# 🔥 These settings force login page on every new browser session

# Session expires when browser closes - KEY SETTING!
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Session timeout in seconds (30 minutes = 1800 seconds)
SESSION_COOKIE_AGE = 1800

# Security cookies
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Don't save session on every request
SESSION_SAVE_EVERY_REQUEST = False

# Clear session on logout
SESSION_CLEAR_ON_LOGOUT = True

# CSRF settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'


# ==================== INTERNATIONALIZATION ====================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ==================== STATIC FILES CONFIGURATION ====================

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ==================== DEFAULT PRIMARY KEY FIELD ====================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
# ems/settings.py - Add these lines

# ==================== SESSION SECURITY ====================
# 🔥 This is how REAL websites work

# Session expires when browser closes (like Gmail)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Session timeout (30 minutes like banking sites)
SESSION_COOKIE_AGE = 1800

# Security settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_CLEAR_ON_LOGOUT = True

# CSRF settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Prevent back button after logout
SECURE_REFERRER_POLICY = 'same-origin'
STATIC_URL = '/static/'

# Email configuration for real sending (Gmail example)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'mrugann950@gmail.com'           # Your Gmail address
EMAIL_HOST_PASSWORD = 'xcxahcvydvemkgnk' # No spaces

"""
Django settings for ui pp. This is just a harness type
project for testing and interacting with the app.


For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/

"""
import ast
import os
import platform

import dj_database_url
import yaml

VERSION = "0.0.0"

CONFIG_PATHS = [
    os.environ.get('MICROMASTERS_CONFIG', ''),
    os.path.join(os.getcwd(), 'micromasters.yml'),
    os.path.join(os.path.expanduser('~'), 'micromasters.yml'),
    '/etc/micromasters.yml',
]


def load_fallback():
    """Load optional yaml config"""
    fallback_config = {}
    config_file_path = None
    for config_path in CONFIG_PATHS:
        if os.path.isfile(config_path):
            config_file_path = config_path
            break
    if config_file_path is not None:
        with open(config_file_path) as config_file:
            fallback_config = yaml.safe_load(config_file)
    return fallback_config

FALLBACK_CONFIG = load_fallback()


def get_var(name, default):
    """Return the settings in a precedence way with default"""
    try:
        value = os.environ.get(name, FALLBACK_CONFIG.get(name, default))
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_var(
    'SECRET_KEY',
    '36boam8miiz0c22il@3&gputb=wrqr2plah=0#0a_bknw9(2^r'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = get_var('DEBUG', False)

ALLOWED_HOSTS = get_var('ALLOWED_HOSTS', [])

SECURE_SSL_REDIRECT = get_var('MICROMASTERS_SECURE_SSL_REDIRECT', True)


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    # Our INSTALLED_APPS
    'ui',
    'courses',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'micromasters.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR + '/templates/'
        ],
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

WSGI_APPLICATION = 'micromasters.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
# Uses DATABASE_URL to configure with sqlite default:
# For URL structure:
# https://github.com/kennethreitz/dj-database-url
DEFAULT_DATABASE_CONFIG = dj_database_url.parse(
    get_var(
        'DATABASE_URL',
        'sqlite:///{0}'.format(os.path.join(BASE_DIR, 'db.sqlite3'))
    )
)

if get_var('MICROMASTERS_DB_DISABLE_SSL', False):
    DEFAULT_DATABASE_CONFIG['OPTIONS'] = {}
else:
    DEFAULT_DATABASE_CONFIG['OPTIONS'] = {'sslmode': 'require'}

DATABASES = {
    'default': DEFAULT_DATABASE_CONFIG
}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

# Serve static files with dj-static
STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ]
}

# Request files from the webpack dev server
USE_WEBPACK_DEV_SERVER = get_var('MICROMASTERS_USE_WEBPACK_DEV_SERVER', False)
WEBPACK_SERVER_URL = get_var('MICROMASTERS_WEBPACK_SERVER_URL', 'http://{host}:8078')

# Important to define this so DEBUG works properly
INTERNAL_IPS = (get_var('HOST_IP', '127.0.0.1'), )

# Configure e-mail settings
EMAIL_BACKEND = get_var('MICROMASTERS_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = get_var('MICROMASTERS_EMAIL_HOST', 'localhost')
EMAIL_PORT = get_var('MICROMASTERS_EMAIL_PORT', 25)
EMAIL_HOST_USER = get_var('MICROMASTERS_EMAIL_USER', '')
EMAIL_HOST_PASSWORD = get_var('MICROMASTERS_EMAIL_PASSWORD', '')
EMAIL_USE_TLS = get_var('MICROMASTERS_EMAIL_TLS', False)
EMAIL_SUPPORT = get_var('MICROMASTERS_SUPPORT_EMAIL', 'support@example.com')
DEFAULT_FROM_EMAIL = get_var('MICROMASTERS_FROM_EMAIL', 'webmaster@localhost')

# e-mail configurable admins
ADMIN_EMAIL = get_var('MICROMASTERS_ADMIN_EMAIL', '')
if ADMIN_EMAIL is not '':
    ADMINS = (('Admins', ADMIN_EMAIL),)
else:
    ADMINS = ()

# Logging configuration
LOG_LEVEL = get_var('MICROMASTERS_LOG_LEVEL', 'DEBUG')
DJANGO_LOG_LEVEL = get_var('DJANGO_LOG_LEVEL', 'DEBUG')

# For logging to a remote syslog host
LOG_HOST = get_var('MICROMASTERS_LOG_HOST', 'localhost')
LOG_HOST_PORT = get_var('MICROMASTERS_LOG_HOST_PORT', 514)

HOSTNAME = platform.node().split('.')[0]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'formatters': {
        'verbose': {
            'format': (
                '[%(asctime)s] %(levelname)s %(process)d [%(name)s] '
                '%(filename)s:%(lineno)d - '
                '[{hostname}] - %(message)s'
            ).format(hostname=HOSTNAME),
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'syslog': {
            'level': LOG_LEVEL,
            'class': 'logging.handlers.SysLogHandler',
            'facility': 'local7',
            'formatter': 'verbose',
            'address': (LOG_HOST, LOG_HOST_PORT)
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'loggers': {
        'root': {
            'handlers': ['console', 'syslog'],
            'level': LOG_LEVEL,
        },
        'ui': {
            'handlers': ['console', 'syslog'],
            'level': LOG_LEVEL,
        },
        'django': {
            'propagate': True,
            'level': DJANGO_LOG_LEVEL,
            'handlers': ['console', 'syslog'],
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': True,
        },
        'urllib3': {
            'level': 'INFO',
        }
    },
}

# status
STATUS_TOKEN = get_var("STATUS_TOKEN", "")
HEALTH_CHECK = ['POSTGRES']

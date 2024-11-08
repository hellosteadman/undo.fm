from pathlib import Path
import dj_database_url
import os


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = not not os.getenv('DEBUG')
DOMAIN = os.getenv('DOMAIN', 'undo.fm')
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'taggit',
    'easy_thumbnails',
    'django_bootstrap5',
    'anymail',
    'django_rq',
    'watson',
    'webmention',
    'sidekick.newsletter',
    'sidekick.front',
    'sidekick.oembed',
    'sidekick.mail',
    'sidekick.theme',
    'sidekick.seo',
    'sidekick.contrib.notion'
]

MIDDLEWARE = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
)

ROOT_URLCONF = 'sidekick.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'sidekick.theme.context_processors.theme'
            ]
        }
    }
]

WSGI_APPLICATION = 'sidekick.wsgi.application'
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///%s' % os.path.join(BASE_DIR, 'db.sqlite')
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'  # NOQA
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'  # NOQA
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'  # NOQA
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'  # NOQA
    }
]

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = False
USE_TZ = True

STATIC_URL = os.getenv('STATIC_URL') or '/static/'
STATIC_ROOT = os.getenv('STATIC_ROOT')
MEDIA_URL = os.getenv('MEDIA_URL') or '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT') or os.path.join(BASE_DIR, 'media')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': MEDIA_ROOT,
            'base_url': MEDIA_URL
        }
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'  # NOQA
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ORIGIN_ALLOW_ALL = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
RQ_QUEUES = {
    'default': {
        'URL': REDIS_URL
    }
}

NOTION = {
    'API_KEY': os.getenv('NOTION_API_KEY'),
    'DATABASES': {
        'newsletter.Post': os.getenv('NOTION_NEWSLETTER_DATABASE'),
        'newsletter.Subscriber': os.getenv('NOTION_SUBSCRIBER_DATABASE'),
        'front.Page': os.getenv('NOTION_PAGE_DATABASE')
    }
}

ANYMAIL = {
    'MAILERSEND_API_TOKEN': os.getenv('MAILERSEND_API_TOKEN'),
    'MAILERSEND_SENDER_DOMAIN': 'undo.fm'
}

EMAIL_BACKEND = 'anymail.backends.mailersend.EmailBackend'
DEFAULT_FROM_NAME = 'Mark Steadman'
DEFAULT_FROM_EMAIL = 'hello@undo.fm'
DEFAULT_REPLYTO_EMAIL = 'hello@undo.fm'

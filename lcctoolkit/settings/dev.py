import environ
from lcctoolkit.settings.base import *  # noqa
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

root = environ.Path(__file__) - 3
env = environ.Env(DEBUG=(bool, False),)

BASE_DIR = root()

SECRET_KEY = env('SECRET_KEY', default='secret')
DEBUG = env('DEBUG')

DATABASES = {
    'default': env.db(default='sqlite:////tmp/my-tmp-sqlite.db'),
}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': env(
            'ELASTICSEARCH_HOST', default='elastic:changeme@elasticsearch:9200')
    },
}

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

STATIC_URL = '/static/'
STATIC_ROOT = env('STATIC_ROOT',
                  default=root.path('lcc/static')())

MEDIA_URL = '/files/'
MEDIA_ROOT = root.path('media/uploadfiles/')()

EMAIL_HOST = 'postfix'
EMAIL_FROM = 'no-reply@climatelawtoolkit.org'

DOMAIN = env('DOMAIN', default='http://localhost:8000')

if not DEBUG:

    # sentry configuration
    SENTRY_DSN = env('SENTRY_DSN', default='')
    SENTRY_ENV = env('SENTRY_ENV', default='')
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENV,
            integrations=[DjangoIntegration()]
        )

    # google analytics
    GA_TRACKING_ID = env('GA_TRACKING_ID', default='')

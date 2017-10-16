import environ
from lcctoolkit.settings import INSTALLED_APPS


root = environ.Path(__file__) - 2
env = environ.Env(DEBUG=(bool, False),)

BASE_DIR = root()

SECRET_KEY = env('SECRET_KEY', default='secret')
DEBUG = env('DEBUG')

DATABASES = {
    'default': env.db(default='sqlite:////tmp/my-tmp-sqlite.db'),
}

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

STATIC_URL = '/static/'
STATIC_ROOT = env('STATIC_ROOT', default='static/')

STATICFILES_DIRS = [
    root.path('static/')()
]

MEDIA_URL = '/files/'
MEDIA_ROOT = root.path('media/uploadfiles/')()

if not DEBUG:

    # sentry configuration
    SENTRY_PUBLIC_DSN = env('SENTRY_PUBLIC_DSN', default='')
    SENTRY_DSN = env('SENTRY_DSN', default='')
    RAVEN_CONFIG = {'dsn': SENTRY_DSN}
    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)

    # google analytics
    GA_TRACKING_ID = env('GA_TRACKING_ID', default='')

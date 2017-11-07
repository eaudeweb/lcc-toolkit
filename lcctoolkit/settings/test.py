import os
import environ
from lcctoolkit.settings.dev import *  # noqa

env = environ.Env(DEBUG=(bool, False),)

if 'TRAVIS' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': 'localhost',
            'NAME': 'test_lcc',
            'PASSWORD': '',
            'PORT': 5432,
            'USER': 'postgres'
        }
    }

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': env(
            'ELASTICSEARCH_HOST',
            default='elastic:changeme@elasticsearch_test:9200'
        )
    },
}

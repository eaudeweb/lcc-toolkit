import environ
from lcctoolkit.settings.dev import *  # noqa

env = environ.Env(DEBUG=(bool, False),)


ELASTICSEARCH_DSL = {
    'default': {
        'hosts': env(
            'ELASTICSEARCH_HOST',
            default='elastic:changeme@elasticsearch_test:9200'
        )
    },
}

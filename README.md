# LawClimateChangeToolkit

A web application which stands as a toolkit for climate change law assessment.

[![Travis](https://travis-ci.org/eaudeweb/lcc-toolkit.svg?branch=develop)](https://travis-ci.org/eaudeweb/lcc-toolkit)
[![Coverage](https://coveralls.io/repos/github/eaudeweb/lcc-toolkit/badge.svg?branch=develop)](https://coveralls.io/github/eaudeweb/lcc-toolkit?branch=develop)
[![Docker](https://dockerbuildbadges.quelltext.eu/status.svg?organization=eaudeweb&repository=lcc-toolkit&tag=dev)](https://hub.docker.com/r/eaudeweb/lcc-toolkit/builds)

## Prerequisites

* Install [Docker](https://www.docker.com/community-edition#/download)
* Install [Docker Compose](https://docs.docker.com/compose/install/)

## Installing the application

1. Get the source code:

        $ git clone https://github.com/eaudeweb/lcc-toolkit
        $ cd lcc-toolkit

1. Customize the environment files:

        $ cp docker/postgres.env.example docker/postgres.env
        $ cp docker/web.env.example docker/web.env
        $ cp docker/init.sql.example docker/init.sql

    Depending on the installation mode, create the docker-compose.override.yml file:

         $ cp docker-compose.override.[prod|dev].yml docker-compose.override.yml

1. Start the application stack:

        $ docker-compose up -d
        $ docker-compose logs

1. Attach to the web service:

        $ docker-compose run web

1. Create a superuser (for Ansible see https://gist.github.com/elleryq/9c70e08b1b2cecc636d6):

        $ docker-compose run --entrypoint bash web
        $ python manage.py createsuperuser

That's it. If you installed in production mode, you should be able to access the
app at http://localhost:8000. If you installed in development mode, follow the
next steps.

## Development setup

Make sure you have the following settings configured correctly (these are the
default values in the .example files, so you shouldn't have to change anything).

* `DEBUG=on` in `web.env` file.

* `entrypoint: bash` in the `docker-compose.override.yml` file's `web` section

Then run the web service

    $ docker-compose run web

and run the following:

        $ ./manage.py migrate
        $ ./manage.py load_fixtures
        $ ./manage.py createsuperuser
        # ./manage.py runserver 0.0.0.0:8000

## Testing

To execute the test suite, attach to the web service and run the following:

    $ pip install -r requirements-dev.txt
    $ python manage.py test

## Configuration variables

The application expects configuration via environment variables:

``DEBUG``
    Turns on debugging behaviour if set to ``on``. Not secure for use in
    production.

``SECRET_KEY``
    Random secret used for Django browser sessions.

``DATABASE_URL``
    Django database connector.

``ALLOWED_HOSTS``
    A list of host/domain names that this Django site can serve.

``SENTRY_DSN``, ``SENTRY_PUBLIC_DSN``
    URL of Sentry server to report errors. Optional.

``GA_TRACKING_ID``
    Google Analytics tracking code. Optional.

``POSTGRES_PASSWORD``
    PostgreSQL superuser password.

``NODE_ENV``
    Define different environments for nodejs. Possible values are: prod, dev.

# LawClimateChangeToolkit

A web application which stands as a toolkit for climate change law assessment.

[![Travis](https://travis-ci.org/eaudeweb/lcc-toolkit.svg?branch=develop)](https://travis-ci.org/eaudeweb/lcc-toolkit)
[![Coverage](https://coveralls.io/repos/github/eaudeweb/lcc-toolkit/badge.svg?branch=develop)](https://coveralls.io/github/eaudeweb/lcc-toolkit?branch=develop)
[![Docker]( https://dockerbuildbadges.quelltext.eu/status.svg?organization=eaudeweb&repository=lcc-toolkit)](https://hub.docker.com/r/eaudeweb/lcc-toolkit/builds)

## Prerequisites

* Install [Docker](https://www.docker.com/community-edition#/download)
* Install [Docker Compose](https://docs.docker.com/compose/install/)

## Installing the application

1. Get the source code:

        $ git clone https://github.com/eaudeweb/lcc-toolkit
        $ cd lcc-toolkit

2. Customize the environment files:

        $ cp docker/postgres.env.example docker/postgres.env
        $ vim docker/postgres.env
        $ cp docker/web.env.example docker/web.env
        $ vim docker/web.env
        $ cp docker/init.sql.example docker/init.sql
        $ vim docker/init.sql
    
    Depending on the installation type, create the docker-compose.override.yml file:

         $ cp docker-compose.override.[prod|dev].yml docker-compose.override.yml
         $ vim docker-compose.override.yml

3. Start the application stack:

        $ docker-compose up -d
        $ docker-compose logs

4. Create a superuser:

        $ docker exec -it lcct.web bash
        $ python manage.py createsuperuser

That's it. You should now be able to access the app at http://localhost:8000.

## Testing

To execute the test suite, attach to the web service:

    $ docker exec -it lcct.web bash

and run the following:

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

``SENTRY_DSN``
    URL of Sentry server to report errors. Optional.

``POSTGRES_PASSWORD``
    PostgreSQL superuser password.

``NODE_ENV``
    Define different environments for nodejs. Possible values are: prod, dev.

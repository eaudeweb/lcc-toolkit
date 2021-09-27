# Law Climate Change Toolkit

A web application which stands as a toolkit for climate change law assessment.

[![Travis](https://travis-ci.org/eaudeweb/lcc-toolkit.svg)](https://travis-ci.org/eaudeweb/lcc-toolkit)
[![Coverage](https://coveralls.io/repos/github/eaudeweb/lcc-toolkit/badge.svg)](https://coveralls.io/github/eaudeweb/lcc-toolkit)
[![Docker](https://dockerbuildbadges.quelltext.eu/status.svg?organization=eaudeweb&repository=lcc-toolkit)](https://hub.docker.com/r/eaudeweb/lcc-toolkit/builds)

## Prerequisites

* Install [Docker](https://www.docker.com/community-edition#/download)
* Install [Docker Compose](https://docs.docker.com/compose/install/)

## Installing the application

1. Get the source code:

        git clone https://github.com/eaudeweb/lcc-toolkit
        cd lcc-toolkit

1. Customize the environment files:

        cp docker/postgres.env.example docker/postgres.env
        cp docker/web.env.example docker/web.env
        cp docker/init.sql.example docker/init.sql

    Depending on the installation mode, create the docker-compose.override.yml file:

        cp docker-compose.override.[prod|dev].yml docker-compose.override.yml

1. Start the application stack:

        docker-compose up -d
        docker-compose logs

1. Attach to the web service:

        docker-compose run web

1. Create a superuser (for Ansible see <https://gist.github.com/elleryq/9c70e08b1b2cecc636d6>)

        python manage.py createsuperuser

That's it. If you installed in production mode, you should be able to access the
app at <http://localhost:8000.> If you installed in development mode, follow the
next steps.

## Development setup

Make sure you have the following settings configured correctly (these are the
default values in the .example files, so you shouldn't have to change anything).

* `DEBUG=on` in `web.env` file.

* The `docker-compose.override.yml` file's `web` section includes this:

      build:
        context: .
        args:
          REQFILE: requirements-dev.txt
      entrypoint: bash

To create and run the develop stack:
    docker-compose up -d
    docker-compose ps
    docker exec -it lcct.web bash

and run the following:

    python manage.py migrate
    python manage.py load_fixtures
    python manage.py createsuperuser
    python manage.py search_index --rebuild
    python manage.py runserver 0.0.0.0:8000

Now you should be able to access the app in development mode at <http://localhost:8000>
By default, there will be no Legislation in the database. In order to generate
some fake legislation for testing/debugging purposes, you can run the following
command:

    python manage.py generate_fake_legislation [N]

Where [N] is the number of Legislation objects to generate.

If you need to make front-end changes, make sure to run:

    grunt dev

## Testing

Allow the user to create a database:
    docker exec -it lcct.db bash
    psql -U postgres
    ALTER USER demo CREATEDB;

To execute the test suite, attach to the web service and run the following:

    python manage.py test

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


## Migrating data to a different server

To create a Postgresql dump directly from the running lcct.db container, the following command should be used:
```shell
docker exec lcct.db pg_dump -U lcct lcct > <backup-file-name>
```
The `-U lcct` part refers to the database user, while the last lcct in the `docker exec` command refers to the database name.

To restore the backed-up data to a fresh install of the lcc-toolkit stack, the following command should be used:
```shell
docker exec lcct.db psql -U lcct lcct < <backup-file-name>
The psql parameters are the same as those used for the above pg_dump command.
```

Migrating Elastic Search from 5.4 to Elastic Search 7.14:

1. For keeping the volume, you will first need to update to Elastic Search 6.8.
   The first step is to use the followin elastic search image: docker.elastic.co/elasticsearch/elasticsearch:6.8.18

1. Add Kibana in the stack: docker.elastic.co/kibana/kibana:6.8.18

1. Install python packages for Elastic Search version 6.8.18
```
pip install django-elasticsearch-dsl==6.5.0
pip install elasticsearch-dsl==6.4.0
pip install elasticsearch==6.8.2
```

1. Reindex the data
```
python manage.py search_index --rebuild
```

1. Use Kibana Upgrade Assistant to reindex the other nodes that weren't indexed by the python package

1. Use Kibana console to upgrade the watches index: POST /_xpack/migration/upgrade/.watches

1. Set elasticsearch to image docker.elastic.co/elasticsearch/elasticsearch:7.14.1 and add the following variable to the environment: discovery.type=single-node

1. Install the python packages required for ElasticSearch 7.4:
```
pip install django-elasticsearch-dsl==7.2.0
pip install elasticsearch-dsl==7.3.0
pip install elasticsearch==7.13.3
```

1. Reindex one last time from the python shell to check if everything is working as expected:
```
python manage.py search_index --rebuild
```

# Generate documentation

The application documentation is generated from Sphinx. The following commands should be run on production
every time the documentation is changed:


    cd docs/
    make html

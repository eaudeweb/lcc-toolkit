# LawClimateChangeToolkit

A web application which stands as a toolkit for climate change law assessment.

## Contributing

Make sure you have [Docker](https://www.docker.com/community-edition#/download)
and [Docker Compose](https://docs.docker.com/compose/install/) installed, then
run:

    $ docker-compose up -d

This will spin up 3 services:

* db
* grunt
* web

In order to setup your local environment, attach to the web service:

    $ docker-compose run web bash

And run the following:

    $ ./manage.py migrate
    $ ./manage.py load_fixtures
    $ ./manage.py createsuperuser

That's it. You should now be able to access the app at http://localhost:8000.

## Testing

To execute the test suite, just run:

    $ ./manage.py test

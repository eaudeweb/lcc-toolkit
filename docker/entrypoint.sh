#!/bin/bash

set -e

until psql $DATABASE_URL -c '\l'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

if [ "x$DJANGO_MANAGEPY_MIGRATE" = 'xon' ]; then
    python manage.py migrate --noinput
fi

if [ "x$DJANGO_MANAGEPY_COLLECTSTATIC" = 'xon' ]; then
    python manage.py collectstatic --noinput
fi

if [ "x$DJANGO_MANAGEPY_LOADFIXTURES" = 'xon' ]; then
    python manage.py load_fixtures
fi

case "$1" in
    manage)
        exec python manage.py "$1"
        ;;
    run)
        exec gunicorn lcctoolkit.wsgi:application \
            --name lcct \
            --bind 0.0.0.0:80 \
            --workers 3 \
            --access-logfile - \
            --error-logfile -
        ;;
    *)
esac
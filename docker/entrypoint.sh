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

if [ "x$GRUNT_TASK" = 'xdev' ]; then
    grunt $GRUNT_TASK &
fi

case "$1" in
    manage)
        exec python manage.py "$1"
        ;;
    run)
        if [ "x$DEBUG" = 'xon' ]; then
            exec python manage.py runserver 0.0.0.0:8000
        else
            exec gunicorn lcctoolkit.wsgi:application \
                    --name lcct \
                    --bind 0.0.0.0:8000 \
                    --timeout $TIMEOUT \
                    --workers 3 \
                    --access-logfile - \
                    --error-logfile -
        fi
        ;;
    *)
esac

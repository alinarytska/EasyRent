#!/bin/sh

set -e

python manage.py migrate
python manage.py collectstatic --noinput

if [ "${CREATE_SUPERUSER_ON_STARTUP:-False}" = "True" ]; then
    python manage.py create_superuser_if_not_exists
fi

if [ "${SEED_DATA_ON_STARTUP:-False}" = "True" ]; then
    python manage.py seed_data ${SEED_DATA_ARGS:-}
fi

exec "$@"

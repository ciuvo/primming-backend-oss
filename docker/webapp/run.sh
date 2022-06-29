#!/bin/bash

HYPERCORN_OPTS="primming.asgi:application -k uvloop -b 0.0.0.0:8000"
HYPERCORN_CMD="bin/hypercorn"

# activate virutalenv
source bin/activate

if [ ${PRIMMING_ENV} == "dev" ]; then
    HYPERCORN_CMD="src/restart.py"
    # update requirements without needing to rebuild the image in dev mode
    pip install -r conf/requirements.txt
elif [ ${PRIMMING_ENV} == "prod" ]; then
    HYPERCORN_OPTS="${HYPERCORN_OPTS} --workers 3"
fi

echo "Wait for database to be ready.."
sh -c './wait-for.sh database:3306'

bin/python src/manage.py migrate --noinput
bin/python src/manage.py create_admin_user
bin/python src/manage.py collectstatic --noinput  # they're served by nginx
echo "Running '${HYPERCORN_CMD} ${HYPERCORN_OPTS}'"
su primming -c "${HYPERCORN_CMD} ${HYPERCORN_OPTS}"


#!/bin/bash

CELERY_OPTS="-A primming worker --concurrency 2"

# activate virutalenv
source bin/activate

if [ ${PRIMMING_ENV} == "dev" ]; then
    CELERY_OPTS="${CELERY_OPTS} --loglevel=DEBUG"
    # update requirements without needing to rebuild the image in dev mode
    pip install -r conf/requirements.txt
elif [ ${PRIMMING_ENV} == "prod" ]; then
    CELERY_OPTS="${CELERY_OPTS} --loglevel=INFO"
fi

echo "Wait for database to be ready.."
sh -c './wait-for.sh database:3306'

python src/manage.py migrate --noinput
python src/manage.py collectstatic --noinput
echo "Running 'celery ${CELERY_OPTS}'"
su primming -c "celery ${CELERY_OPTS}"


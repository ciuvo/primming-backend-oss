# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# NOTE: this Dockerfile must be run from within the "context" of the project's root directory
# $> docker build -f docker/webapp/Dockerfile .
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
FROM python:3.9

# send output from python straight to stdout
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /opt/primming/src
ENV DJANGO_SETTINGS_MODULE primming.settings
ENV PRIMMING_ENV dev

# create the runtime user + home directory
# install netcat as dependency for waitfor.sh
RUN mkdir -p /opt/primming && \
    addgroup primming && \
    useradd -g primming -d /opt/primming primming && \
    apt-get update && apt-get install -y netcat && \
    apt-get autoremove && apt-get autoclean && apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# copy source
WORKDIR /opt/primming/
COPY conf ./conf/
COPY docker/webapp/run.sh docker/webapp/run-celery.sh docker/webapp/wait-for.sh ./

# Install python dependencies
RUN python -m venv . && . bin/activate && pip install -U pip && \
    pip install --no-cache-dir -r conf/requirements.txt && \
    chown -R primming:primming /opt/primming/ && chmod +x run.sh wait-for.sh run-celery.sh

COPY src ./src/

RUN python -m venv . && . bin/activate && python src/manage.py collectstatic --noinput

# Webapp command
EXPOSE 8000
CMD ./run.sh

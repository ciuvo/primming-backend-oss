# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import os
from datetime import datetime
from typing import Mapping

import django
from django.conf import settings
from fabric2 import task
from invoke import Context

DOCKER_REPOSITORY = "primming"
DOCKER_CUSTOM_IMAGES = ("webapp", "proxy", "database")

BUILD_DEB_PGK_NAME = "primming-backend"
INSTALL_DIR = "/opt/primming-docker/"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

ENVIRONMENT_DEV = "dev"
ENVIRONMENT_PROD = "prod"
ENVIRONMENT = os.environ.get("PRIMMING_ENV", ENVIRONMENT_DEV)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primming.settings")
django.setup()

DOCKER_REGISTRY = settings.DOCKER_REGISTRY


class DockerEnvFile:
    """read, parse & write the .env file"""

    def __init__(self, path: str = os.path.join(ROOT_DIR, ".env")):
        self.path = path
        self.data = self._parse()

    def _parse(self) -> Mapping[str, str]:
        """parse the key=value type file"""
        with open(self.path, "r") as env_file:
            return dict([line.strip().split("=") for line in env_file])

    def save(self) -> None:
        """write the data back to the file"""
        with open(self.path, "w") as env_file:
            for k, v in self.data.items():
                env_file.write("{key}={value}\n".format(key=k, value=v))

    def update_build_version(self, write: bool = True) -> None:
        """
        update the BUILD_VERSION with the current timestamp
        :param write: if true the file will be written back to the disk
        """
        self.data["BUILD_VERSION"] = datetime.now().strftime("%Y.%m.%d.%H%M")
        if write:
            self.save()

    @property
    def build_version(self) -> str:
        return self.data["BUILD_VERSION"]


@task
def build_images(connection, push=False, registry=DOCKER_REGISTRY, repo=DOCKER_REPOSITORY):
    """Build the docker images, if --push is given it is pused to --registry and --repo"""
    env_file = DockerEnvFile()
    local = Context()

    if ENVIRONMENT == ENVIRONMENT_PROD:
        override_file = "docker-compose.prod.yaml"
        env_file.update_build_version()
        local.run("git commit .env -m 'build_images task: update build version'")
    else:
        override_file = "docker-compose.override.yaml"

    local.run(
        (
            "PRIMMING_DOCKER_REGISTRY={docker_registry} docker-compose -p primming -f "
            "docker-compose.yaml -f docker-compose.build.yaml -f {override_file} build"
        ).format(override_file=override_file, docker_registry=DOCKER_REGISTRY)
    )

    if push:
        push_images(connection, registry=registry, repo=repo)


@task
def push_images(connection, registry=DOCKER_REGISTRY, repo=DOCKER_REPOSITORY):
    """Push images to the repo specified in conf/localsettings.yaml or via --registry and --repo"""

    if ENVIRONMENT != ENVIRONMENT_PROD:
        print("WARNING: cannot push in the DEV environment")
    else:
        env_file = DockerEnvFile()
        local = Context()

        # log into AWS registry
        local.run(
            "$(aws ecr get-login --profile primming --no-include-email --region eu-central-1)"
        )

        for image in DOCKER_CUSTOM_IMAGES:
            cmd = "docker push {registry}/{repo}/{image}:{tag}".format(
                registry=registry, repo=repo, image=image, tag=env_file.build_version
            )
            print(cmd)
            local.run(cmd)


@task
def test(connection):
    """Run tests locally

    ..code-block:: shell

        PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings fab2 test

    """
    with connection.cd(ROOT_DIR):
        connection.run(
            'PYTHONPATH="src" PRIMMING_ENV=dev DJANGO_SETTINGS_MODULE=primming.settings '
            "pytest -s src"
        )


@task
def build(connection):
    """build debian package

    Not supported for use by external partners.
    """
    from fabric.api import env
    from pyciuvo.fabric.tasks.pbuilder import BuildDeb

    # fabric 1.x compatibility
    env.host_string = "{user}@{host}".format(user=connection.user, host=connection.host)

    build_images(connection, push=True)

    class LocalBuilder(BuildDeb):
        def get_template_context(self, template, outpath):
            context = super().get_template_context(template, outpath)
            context["PKG_NAME"] = BUILD_DEB_PGK_NAME
            context["INSTALL_DIR"] = INSTALL_DIR
            context["ENVIRONMENT"] = ENVIRONMENT
            context["DOCKER_REGISTRY"] = DOCKER_REGISTRY
            return context

        def run(self, *args, **kwargs):
            super().run(*args, **kwargs)

    LocalBuilder(
        config_variable="PRIMMING_ENV",
        pbuilder_dist="xenial",
        pbuilder_arch="i386",
        apt_component="primming",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
        local_pip=False,
        requirements_file="conf/requirements.txt",
    ).run()


@task
def db_dump(connection):
    """
    Dump the webapp's database from the host specified with -H

    ..code-block:: shell

        PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings fab2 db-dump -H primming.picky.io

    """
    filename = "dumps/{}-full.sql.gz".format(datetime.now().strftime("%Y-%m-%d-%H%M"))

    with open("docker/secrets/mysql-pass.txt", "r") as fh:
        password = fh.read().strip()

    # todo load credentials from secrets
    dumpcmd = (
        "sudo docker container exec primming_database_1 mysqldump "
        "-u primmingweb -p{password} primmingweb".format(password=password)
    )

    local = Context()
    local.run("ssh {} '{}| gzip' > {}".format(connection.host, dumpcmd, filename))

    print("Wrote dump to {}".format(filename))


@task
def load_fixtures(connection, docker=True):
    """Load the basic data / form into the database, use --docker for docker or --no-docker for
    local loading."""

    cmd = (
        "PRIMMING_ENV={env} PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings"
        "ls conf/fixtures/0* | sort | xargs python src/manage.py loaddata".format(env=ENVIRONMENT)
    )

    if docker:
        cmd = (
            "PRIMMING_ENV={env} ls conf/fixtures/0* | sort | xargs docker-compose run --rm webapp "
            "bin/python src/manage.py loaddata"
        ).format(env=ENVIRONMENT)

    local = Context()

    with local.cd(ROOT_DIR):
        local.run(cmd, pty=False)


@task
def createsuperuser(connection, docker=True):
    """Load the basic data / form into the database, use --docker for docker or --no-docker for
    local loading."""

    cmd = (
        "PRIMMING_ENV={env} PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings "
        "python src/manage.py createsuperuser"
    ).format(env=ENVIRONMENT)

    if docker:
        cmd = (
            "PRIMMING_ENV={env} docker-compose run --rm -it webapp "
            "bin/python src/manage.py createsuperuser"
        ).format(env=ENVIRONMENT)

    local = Context()

    with local.cd(ROOT_DIR):
        local.run(cmd, pty=True)

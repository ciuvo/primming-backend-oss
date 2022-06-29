# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import os
from datetime import timedelta
from logging.config import dictConfig
from typing import List

import celery
import yaml
from celery import signals
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "primming.settings")
app = celery.Celery("primming")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


def get_schedule(*paths: List[str]) -> dict:
    """Get a Celery beat schedule from the given YAML files.

    To use the schedule, you would typically include it in your ``celery.py``, for example::

        # ...
        app.config_from_object('django.conf:settings')
        app.conf.update(
            CELERYBEAT_SCHEDULE=get_schedule(
                'conf/prod/celery.yaml', 'conf/celery.yaml')
        )


    :param paths: List[str]
        Paths to YAML files that contain celery schedules. Tasks in a successive file will
        overwrite any task in a previous file with the same name. Files that don't exist are
        silently ignored.
    """
    data = {}
    schedules = {}

    for path in paths:
        if os.path.exists(path):
            with open(path) as schedule:
                data.update(yaml.load(schedule, Loader=yaml.FullLoader))

    for name, config in data.items():
        if config is None or not config.get("enabled", True):
            continue

        typ = config["schedule"]["type"]
        opts = config["schedule"]["options"]
        if typ == "crontab":
            schedule = crontab(**opts)
        elif typ == "interval":
            kwargs = {
                opts.get("period", "seconds"): opts["every"],
            }
            schedule = timedelta(**kwargs)
        else:
            raise ValueError("%s: Unknown schedule type." % typ)

        schedules[name] = {
            "task": config["task"],
            "schedule": schedule,
        }
        if config.get("args"):
            schedules[name]["args"] = config["args"]
        if config.get("kwargs"):
            schedules[name]["kwargs"] = config["kwargs"]

    return schedules


app.conf.update(beat_schedule=get_schedule())


@signals.setup_logging.connect
def on_celery_setup_logging(**kwargs):
    dictConfig(settings.LOGGING)


if __name__ == "__main__":
    app.start()

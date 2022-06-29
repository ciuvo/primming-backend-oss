# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import celery


class AutoRegisterTask(celery.Task):
    def __init_subclass__(cls, **kwargs):
        """Because the good people at celery HQ removed the autoregister class based task support.

        https://docs.celeryproject.org/en/v4.0.0/reference/celery.app.task.html#celery.app.task.Task
        """
        cls.name = "%s.%s" % (cls.__module__, cls.__name__)
        super().__init_subclass__(**kwargs)
        celery.current_app.tasks.register(cls)

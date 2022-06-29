# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    You can't really execute commands / open a shell in a fargate container, use this
    https://www.agiliq.com/blog/2019/02/django-aws-fargate-aurora-serverless/
    """

    help = "Creates the initial admin user, disable after you've created the first proper one"

    def handle(self, *args, **options):
        if User.objects.filter(username="InitialAdmin").exists():
            print("admin exists")
        else:
            u = User(username="InitialAdmin")
            u.set_password("DisAbleM3")
            u.is_superuser = True
            u.is_staff = True
            u.save()
            print("admin created")
        sys.exit()

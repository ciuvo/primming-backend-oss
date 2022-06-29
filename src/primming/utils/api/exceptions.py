# -*- coding: utf-8 -*-
# vim: set formatoptions+=l tw=99:
#
# Copyright 2019 Ciuvo GmbH. All rights reserved. This file is subject to the terms and conditions
# defined in file 'LICENSE', which is part of this source code package.
class BadRequestException(Exception):
    """Because django has an exception for 404 but not for others"""

    pass


class NotFoundException(Exception):
    """Because django has an exception for 404 but not for others"""

    pass

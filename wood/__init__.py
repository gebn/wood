# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from pkg_resources import get_distribution, DistributionNotFound
import os


__title__ = 'wood'
__author__ = 'George Brighton'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 George Brighton'


# adapted from http://stackoverflow.com/a/17638236
try:
    dist = get_distribution(__title__)
    path = os.path.normcase(dist.location)
    pwd = os.path.normcase(__file__)
    if not pwd.startswith(os.path.join(path, __title__)):
        raise DistributionNotFound()
    __version__ = dist.version
except DistributionNotFound:
    __version__ = 'unknown'

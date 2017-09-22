# -*- coding: utf-8 -*-
import os
from pkg_resources import get_distribution, DistributionNotFound

from wood.comparison import Comparison as _Comparison
from wood.entities import Root as _Root

from wood.integrations import cloudflare, cloudfront, s3
compare = _Comparison.compare
root = _Root.from_path

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

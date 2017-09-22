# -*- coding: utf-8 -*-
import os

import pathlib
from typing import Union

from pkg_resources import get_distribution, DistributionNotFound

from wood.entities import Root as _Root, Entity as _Entity

from wood.comparison import Comparison
from wood.integrations import cloudflare, cloudfront, s3
root = _Root.from_path
entity = _Entity.from_path

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


def compare(left: Union[str, pathlib.Path, _Entity],
            right: Union[str, pathlib.Path, _Entity]) -> Comparison:
    """
    Compare two paths.

    :param left: The left side or "before" entity.
    :param right: The right side or "after" entity.
    :return: A comparison details what has changed from the left side to the
             right side.
    """

    def normalise(param: Union[str, pathlib.Path, _Entity]) -> _Entity:
        """
        Turns any one of a number of types of input into an entity.

        :param param: The input - either a path string, a path object, or a
                      full blown entity.
        :return: The input param as an entity.
        """
        if isinstance(param, str):
            param = pathlib.Path(param)
        if isinstance(param, pathlib.Path):
            param = entity(param)
        return param

    return Comparison.compare(normalise(left), normalise(right))

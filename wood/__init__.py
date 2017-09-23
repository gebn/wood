# -*- coding: utf-8 -*-
from typing import Union
from pkg_resources import get_distribution, DistributionNotFound
import os
import pathlib

from wood.entities import Root as _Root, Entity as _Entity

from wood.comparison import Comparison
from wood.integrations import cloudflare, cloudfront, s3

__title__ = 'wood'
__author__ = 'George Brighton'
__license__ = 'MIT'
__copyright__ = 'Copyright 2017 George Brighton'


# adapted from http://stackoverflow.com/a/17638236
try:
    dist = get_distribution(__title__)
    dist_path = os.path.normcase(dist.location)
    pwd = os.path.normcase(__file__)
    if not pwd.startswith(os.path.join(dist_path, __title__)):
        raise DistributionNotFound()
    __version__ = dist.version
except DistributionNotFound:
    __version__ = 'unknown'


def _normalise_path(path: Union[str, pathlib.Path]) -> pathlib.Path:
    """
    Ensures a path is parsed.

    :param path: A path string or Path object.
    :return: The path as a Path object.
    """
    if isinstance(path, str):
        return pathlib.Path(path)
    return path


def root(path: Union[str, pathlib.Path]) -> _Root:
    """
    Retrieve a root directory object from a path.

    :param path: The path string or Path object.
    :return: The created root object.
    """
    return _Root.from_path(_normalise_path(path))


def entity(path: Union[str, pathlib.Path]) -> _Entity:
    """
    Retrieve an appropriate entity object from a path.

    :param path: The path of the entity to represent, either a string or Path
                 object.
    :return: An entity representing the input path.
    """
    return _Entity.from_path(_normalise_path(path))


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
            param = _Entity.from_path(param)
        return param

    return Comparison.compare(normalise(left), normalise(right))

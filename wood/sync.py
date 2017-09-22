# -*- coding: utf-8 -*-
from typing import TypeVar, Generic
import abc

from wood.comparison import Comparison
from wood.entities import Entity

L = TypeVar('L', bound=Entity)
R = TypeVar('R', bound=Entity)


class Syncer(Generic[L, R], metaclass=abc.ABCMeta):
    """
    Implemented by things that know how to enact the changes in a comparison
    somewhere.
    """

    def sync(self, comparison: Comparison[L, R]) -> None:
        """
        Synchronise based on the changes in a comparison.

        :param comparison: The comparison to enact.
        """
        raise NotImplementedError()

# -*- coding: utf-8 -*-
from typing import Iterator
import abc

from wood.comparison import Comparison
from wood.entities import Entity


class Invalidator(metaclass=abc.ABCMeta):
    """
    Implemented by things that know how to invalidate the changes in a
    comparison.
    """

    def invalidate(self, comparison: Comparison[Entity, Entity]) -> None:
        """
        Invalidate as necessitated by a comparison.

        :param comparison: The comparison whose changes to invalidate.
        """
        raise NotImplementedError()


class PrefixInvalidator(Invalidator, metaclass=abc.ABCMeta):
    """
    Implemented by things that can invalidate a regex-like prefix suffixed with
    an asterisk. This allows a more efficient (and cheaper) invalidation by
    grouping paths together where possible.
    """

    def invalidate(self, comparison: Comparison[Entity, Entity]) -> None:
        self._invalidate_prefixes(comparison.invalidations())

    @abc.abstractmethod
    def _invalidate_prefixes(self, prefixes: Iterator[str]) -> None:
        """
        Purge a collection of prefixes.

        :param prefixes: The collection of prefixes to purge. These will
                         resemble relative paths that may or may not end with
                         an asterisk, meaning a wildcard.
        """
        raise NotImplementedError()

# -*- coding: utf-8 -*-
from typing import Dict, Tuple, Optional, TypeVar, Iterable

import itertools
import more_itertools

A = TypeVar('A')
B = TypeVar('B')


def zip_dict(a: Dict[str, A], b: Dict[str, B]) \
        -> Dict[str, Tuple[Optional[A], Optional[B]]]:
    """
    Combine the values within two dictionaries by key.

    :param a: The first dictionary.
    :param b: The second dictionary.
    :return: A dictionary containing all keys that appear in the union of a and
             b. Values are pairs where the first part is a's value for the key,
             and right second part b's value.
    """
    return {key: (a.get(key), b.get(key)) for key in a.keys() | b.keys()}


def chunk(iterable: Iterable[A], n: int) \
        -> Iterable[more_itertools.more.peekable]:
    """
    Produce an iterable of interables of a maximum length from a (presumably
    longer) iterable. This is useful when only so many elements can be
    processed at once, such as an API that limits to n things per request.

    :param iterable: The iterable to chunk into iterables of size up to n.
    :param n: The maximum length of each iterable.
    :return: An iterable of iterables. Each iterable will be of size n, except
             possibly the last one which will contain fewer elements.
    """
    iterator = iter(iterable)
    while True:
        chunk_ = more_itertools.peekable(itertools.islice(iterator, n))
        try:
            chunk_.peek()
        except StopIteration:
            return
        yield chunk_

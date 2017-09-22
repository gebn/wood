# -*- coding: utf-8 -*-
from typing import Generic, TypeVar, Iterator, IO, Optional, Dict
import abc
import sys
import pathlib
import itertools

import os

from wood import util
from wood.entities import Entity, File, Directory

L = TypeVar('L', bound=Entity)
R = TypeVar('R', bound=Entity)
L1 = TypeVar('L1', bound=Entity)
R1 = TypeVar('R1', bound=Entity)


class Comparison(Generic[L, R], metaclass=abc.ABCMeta):
    """
    Represents a comparison between any two entities, e.g. a File and a File,
    a File and Directory etc.
    """

    # the number of spaces to indent per level
    _INDENT_SIZE = 4

    def __init__(self, left: Optional[L], right: Optional[R]):
        """
        Initialise a new comparison.

        :param left: The left or "original"/"old" entity. Omit if the entity
                     is new.
        :param right: The right or "current"/"new" entity. Omit if the entity
                      has been deleted.
        :raises ValueError: If both the left and right entities are None.
        """
        if left is None and right is None:
            raise ValueError('The left and right side cannot both be None')
        self.left = left
        self.right = right

    @property
    def is_empty(self) -> bool:
        """
        Find whether this entity is empty.

        :return: True if the entity is empty, false otherwise.
        """
        raise NotImplementedError()

    @property
    def is_new(self) -> bool:
        """
        Find whether this comparison represents a new file.

        :return: True if the right is a new file, false otherwise.
        """
        return self.left is None

    def new(self, base: pathlib.PurePath = pathlib.PurePath(),
            include_intermediates: bool = True) -> Iterator[str]:
        """
        Find the list of new paths in this comparison.

        :param base: The base directory to prepend to the right entity's name.
        :param include_intermediates: Whether to include new non-empty
                                      directories in the returned iterable. If
                                      you only care about files, or are using
                                      flat key-based storage system like S3
                                      where directories are a made-up concept,
                                      this can be set to false.
        :return: An iterator of the new paths.
        """
        if self.is_new:
            yield str(base / self.right.name)

    @property
    @abc.abstractmethod
    def is_modified(self) -> bool:
        """
        Find whether this comparison is for a modified file. Note that
        directory comparisons are always not modified, as a directory itself
        can only be added (new) or removed (deleted).

        :return: True if this comparison represents a modified file, false
                 otherwise.
        """
        raise NotImplementedError()

    def modified(self, base: pathlib.PurePath = pathlib.PurePath()) \
            -> Iterator[str]:
        """
        Find the paths of modified files. There is no option to include
        intermediate directories, as all files and directories exist in both
        the left and right trees.

        :param base: The base directory to recursively append to the right
                     entity.
        :return: An iterable of paths of modified files.
        """
        # N.B. this method will only ever return files, as directories cannot
        # be "modified"
        if self.is_modified:
            yield str(base / self.right.name)

    @property
    def is_deleted(self) -> bool:
        """
        Find whether this comparison represents a deleted entity.

        :return: True if the left entity has been deleted, false otherwise.
        """
        return self.right is None

    def deleted(self, base: pathlib.PurePath = pathlib.PurePath(),
                include_children: bool = True,
                include_directories: bool = True) -> Iterator[str]:
        """
        Find the paths of entities deleted between the left and right entities
        in this comparison.

        :param base: The base directory to recursively append to entities.
        :param include_children: Whether to recursively include children of
                                 deleted directories. These are themselves
                                 deleted by definition, however it may be
                                 useful to the caller to list them explicitly.
        :param include_directories: Whether to include directories in the
                                    returned iterable.
        :return: An iterable of deleted paths.
        """
        if self.is_deleted:
            yield str(base / self.left.name)

    @property
    @abc.abstractmethod
    def invalidate(self) -> bool:
        """
        Find whether this entity should be invalidated.

        :return: True if it should be, false otherwise.
        """
        raise NotImplementedError()

    def invalidations(self) -> Iterator[str]:
        """
        Get a set of invalidation prefixes for this entity and its children.
        These prefixes will resemble relative paths - they will not have a
        leading slash.

        :return: The set of invalidations.
        """
        if self.invalidate:
            yield self.left.name

    @staticmethod
    def compare(left: Optional[L], right: Optional[R]) -> 'Comparison[L, R]':
        """
        Calculate the comparison of two entities.

        | left      | right     | Return Type             |
        |===========|===========|=========================|
        | file      | file      | FileComparison          |
        | file      | directory | FileDirectoryComparison |
        | file      | None      | FileComparison          |
        | directory | file      | DirectoryFileComparison |
        | directory | directory | DirectoryComparison     |
        | directory | None      | DirectoryComparison     |
        | None      | file      | FileComparison          |
        | None      | directory | DirectoryComparison     |
        | None      | None      | TypeError               |

        :param left: The left side or "before" entity.
        :param right: The right side or "after" entity.
        :return: See table above.
        """
        if isinstance(left, File) and isinstance(right, Directory):
            return FileDirectoryComparison(left, right)

        if isinstance(left, Directory) and isinstance(right, File):
            return DirectoryFileComparison(left, right)

        if isinstance(left, File) or isinstance(right, File):
            return FileComparison(left, right)

        if isinstance(left, Directory) or isinstance(right, Directory):
            return DirectoryComparison(left, right)

        raise TypeError(f'Cannot compare entities: {left}, {right}')

    def print_hierarchy(self, level: int = 0, file: IO[str] = sys.stdout) \
            -> None:
        """
        Print this comparison and its children with indentation to represent
        nesting.

        :param level: The level of indentation to use. This is mostly for
                      internal use, but you can use it to inset the root
                      comparison.
        :param file: The stream to print to. Defaults to stdout.
        """
        print(' ' * self._INDENT_SIZE * level + str(self), file=file)

    def __str__(self):
        return f'{self.__class__.__name__}(' \
               f'{self.left or None}|{self.right or None}, ' \
               f'is_new: {self.is_new}, ' \
               f'is_modified: {self.is_modified}, ' \
               f'is_deleted: {self.is_deleted}, ' \
               f'invalidate: {self.invalidate})'


class FileComparison(Comparison[File, File]):
    """
    A comparison of two files.
    """

    @property
    def is_empty(self) -> bool:
        # we have no insight into the contents of files
        return False

    @property
    def is_modified(self) -> bool:
        """
        Find whether the files on the left and right are different. Note,
        modified implies the contents of the file have changed, which is
        predicated on the file existing on both the left and right. Therefore
        this will be false if the file on the left has been deleted, or the
        file on the right is new.

        :return: Whether the file has been modified.
        """
        if self.is_new or self.is_deleted:
            return False
        return self.left.md5 != self.right.md5

    @property
    def invalidate(self) -> bool:
        return self.is_modified or self.is_deleted

    def __init__(self, left: Optional[File], right: Optional[File]):
        """
        Initialise a new file comparison.

        :param left: The "original" or "old" file. Cannot be None if right is
                     None.
        :param right: The "current" or "new" file. Cannot be None if left is
                      None.
        """
        super().__init__(left, right)


class DirectoryComparison(Comparison[Directory, Directory]):
    """
    A comparison of two directories.
    """

    @property
    def is_empty(self) -> bool:
        return not self.children

    def new(self, base: pathlib.PurePath = pathlib.PurePath(),
            include_intermediates: bool = True) -> Iterator[str]:

        # if the RHS has been deleted, there's nothing to do, so yield nothing
        if self.is_deleted:
            return

        us = base / self.right.name

        # if we ourselves are new, we need to return our path, as long as we
        # don't have any children, unless include_intermediates is
        # true
        if self.is_new and (not self.children or include_intermediates):
            # we have no children, or we do but include_intermediates is true
            # N.B. we can guarantee intermediate directories will be seen
            # before their children
            yield str(us) + '/'

        # we need to return all new paths in our children
        # N.B. if we are new, all of our children have to be new by definition
        yield from itertools.chain.from_iterable(
            [child.new(us, include_intermediates)
             for child in self.children.values()])

    @property
    def is_modified(self) -> bool:
        # we regard directories as containers - they can be new or deleted, but
        # never modified
        return False

    def modified(self, base: pathlib.PurePath = pathlib.PurePath()) \
            -> Iterator[str]:
        # given we cannot be modified, provided we are not deleted, we simply
        # delegate to our children
        if not self.is_deleted:
            us = base / self.right.name
            yield from itertools.chain.from_iterable(
                [child.modified(us) for child in self.children.values()])

    def deleted(self, base: pathlib.PurePath = pathlib.PurePath(),
                include_children: bool = True,
                include_directories: bool = True) -> Iterator[str]:
        if self.is_new:
            return  # no self.left

        us = base / self.left.name

        if self.is_deleted and include_directories:
            yield str(us) + '/'

        if not self.is_deleted or include_children:
            yield from itertools.chain.from_iterable(
                [child.deleted(us, include_children, include_directories)
                 for child in self.children.values()])

    def __init__(self, left: Optional[Directory], right: Optional[Directory]):
        super().__init__(left, right)
        left_children = {} if left is None else left.children
        right_children = {} if right is None else right.children
        self.children = {
            name: Comparison.compare(l, r)
            for name, (l, r) in
            util.zip_dict(
                left_children,
                right_children).items()}  # type: Dict[str, Comparison[Entity]]

    def print_hierarchy(self, level: int = 0, file: IO[str] = sys.stdout) \
            -> None:
        super().print_hierarchy(level, file)
        for child in self.children.values():
            child.print_hierarchy(level + 1, file)

    @property
    def invalidate(self) -> bool:
        # N.B. the case of no children is interesting:
        #  - if we allow ourselves to be invalidated, this allows the
        #    possibility of an aggregation on our parent directory
        #  - however, if that aggregation could not be done, we've incurred an
        #    explicit invalidation ($0.005) for ourselves for no reason
        # So it's not cut and dry. This method goes for the first case, and we
        # account for the second later.
        return all([child.invalidate for child in self.children.values()])

    def invalidations(self) -> Iterator[str]:
        name = self.right.name if self.is_new else self.left.name
        if self.invalidate:
            # could also just `yield name + '*'`, however this could
            # over-invalidate if multiple directories have a prefix of `name`

            # hack: the root directory is an empty string; we shouldn't have to
            # worry about this here
            if name:
                yield name

            yield os.path.join(name, '*')
        else:
            child_invalidations = itertools.chain.from_iterable(
                [child.invalidations()
                 for child in self.children.values()
                 if not child.is_empty])  # exclude unchanged empty directories
            yield from [os.path.join(name, invalidation)
                        for invalidation in child_invalidations]


class ReplacementComparison(Comparison[L, R], Generic[L, R],
                            metaclass=abc.ABCMeta):
    """
    A comparison between two entities of differing types. Due to the
    incompatibility, we simply treat this as the left entity being deleted,
    and the right entity being new.
    """

    @property
    def is_new(self) -> bool:
        return True

    @property
    def is_modified(self) -> bool:
        return False

    @property
    def is_deleted(self) -> bool:
        return True

    @property
    def invalidate(self) -> bool:
        return True

    def __init__(self, left: L, right: R,
                 children: Dict[str, Comparison[L1, R1]]):
        super().__init__(left, right)
        self.children = children

    def print_hierarchy(self, level: int = 0, file: IO[str] = sys.stdout) \
            -> None:
        super().print_hierarchy(level, file)
        for child in self.children.values():
            child.print_hierarchy(level + 1, file)


class FileDirectoryComparison(ReplacementComparison[File, Directory]):
    """
    The comparison of a file and directory.
    """

    @property
    def is_empty(self) -> bool:
        return not self.right.children

    def new(self, base: pathlib.PurePath = pathlib.PurePath(),
            include_intermediates: bool = True) -> Iterator[str]:
        us = base / self.right.name

        # if we ourselves are new, we need to return our path, as long as we
        # don't have any children, unless include_intermediates is
        # true
        if not self.children or include_intermediates:
            # we have no children, or we do but include_intermediates is true
            # N.B. we can guarantee intermediate directories will be seen
            # before their children
            yield str(us) + '/'

        # we need to return all new paths in our children
        # N.B. if we are new, all of our children have to be new by definition
        yield from itertools.chain.from_iterable(
            [child.new(us, include_intermediates)
             for child in self.children.values()])

    def __init__(self, left: File, right: Directory):
        super().__init__(left, right,
                         {name: Comparison.compare(None, r)
                          for name, r in right.children.items()})


class DirectoryFileComparison(ReplacementComparison[Directory, File]):
    """
    The comparison of a directory and file.
    """

    @property
    def is_empty(self) -> bool:
        return False

    def deleted(self, base: pathlib.PurePath = pathlib.PurePath(),
                include_children: bool = True,
                include_directories: bool = True) -> Iterator[str]:
        us = base / self.left.name

        if self.is_deleted and include_directories:
            yield str(us) + '/'

        if not self.is_deleted or include_children:
            yield from itertools.chain.from_iterable(
                [child.deleted(us, include_children, include_directories)
                 for child in self.children.values()])

    def invalidations(self) -> Iterator[str]:
        if self.invalidate:
            yield self.left.name + '/*'

    def __init__(self, left: Directory, right: File):
        super().__init__(left, right,
                         {name: Comparison.compare(l, None)
                          for name, l in left.children.items()})

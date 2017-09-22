# -*- coding: utf-8 -*-
import abc
import hashlib
import itertools
import pathlib
import sys
from typing import Optional, IO, Iterator, Dict


class Entity(metaclass=abc.ABCMeta):
    """
    Represents a snapshot of a file or directory.
    """

    # the number of spaces to indent per level
    _INDENT_SIZE = 4

    def __init__(self, name):
        """
        Initialise a new entity.

        :param name: The name of the entity, e.g. "essay.txt" or "photos".
        """
        self.name = name

    @abc.abstractmethod
    def walk_paths(self,
                   base: Optional[pathlib.PurePath] = pathlib.PurePath()) \
            -> Iterator[pathlib.PurePath]:
        """
        Recursively traverse all paths inside this entity, including the entity
        itself.

        :param base: The base path to prepend to the entity name.
        :return: An iterator of paths.
        """
        raise NotImplementedError()

    def _walk_paths(self, base: pathlib.PurePath) \
            -> Iterator[pathlib.PurePath]:
        """
        Internal helper for walking paths. This is required to exclude the name
        of the root entity from the walk.

        :param base: The base path to prepend to the entity name.
        :return: An iterator of paths.
        """
        return self.walk_paths(base)

    @abc.abstractmethod
    def walk_files(self) -> Iterator['File']:
        """
        Recursively traverse all files inside this entity, including the entity
        itself.

        :return: An iterator of files.
        """
        raise NotImplementedError()

    @classmethod
    def from_path(cls, path: pathlib.Path) -> 'Entity':
        """
        Create an entity from a local path.

        :param path: The path to the entity, either a file or directory.
        :return: An entity instance representing the path.
        """
        if path.is_file():
            return File.from_path(path)
        return Directory.from_path(path)

    def print_hierarchy(self, level: int = 0, file: IO[str] = sys.stdout) \
            -> None:
        """
        Print this entity and its children with indentation to represent
        nesting.

        :param level: The level of indentation to use. This is mostly for
                      internal use, but you can use it to inset the root
                      entity.
        :param file: The stream to print to. Defaults to stdout.
        """
        print(' ' * self._INDENT_SIZE * level + str(self), file=file)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.name})'

    def __repr__(self) -> str:
        return f'<{self}>'


class File(Entity):
    """
    Represents a file.
    """

    def __init__(self, name, size, md5):
        """
        Initialise a new file entity.

        :param name: The file name, including extension if any.
        :param size: The size of the file in bytes.
        :param md5: The lowercase hex representation of the file's MD5
                    checksum. Should be exactly 32 chars long.
        """
        super().__init__(name)
        self.size = size
        self.md5 = md5

    def walk_paths(self,
                   base: Optional[pathlib.PurePath] = pathlib.PurePath()) \
            -> Iterator[pathlib.PurePath]:
        yield base / self.name

    def walk_files(self) -> Iterator['File']:
        yield self

    @staticmethod
    def _md5(path: pathlib.PurePath):
        """
        Calculate the MD5 checksum of a file.

        :param path: The path of the file whose checksum to calculate.
        :return: The lowercase hex representation of the file's MD5
                    checksum, exactly 32 chars long.
        """
        hash_ = hashlib.md5()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_.update(chunk)
        return hash_.hexdigest()

    @classmethod
    def from_path(cls, path: pathlib.Path) -> 'File':
        """
        Create a file entity from a file path.

        :param path: The path of the file.
        :return: A file entity instance representing the file.
        :raises ValueError: If the path does not point to a file.
        """
        if not path.is_file():
            raise ValueError('Path does not point to a file')
        return File(path.name, path.stat().st_size, cls._md5(path))

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.name}, {self.size}, ' \
               f'{self.md5})'


class Directory(Entity):
    """
    Represents a directory.
    """

    def __init__(self, name, children: Optional[Dict[str, Entity]] = None):
        """
        Initialise a new directory entity.

        :param name: The name of the directory, e.g. "photos".
        :param children: Entities within this directory. Keys are entity names,
                         whose values correspond to the entity object. Defaults
                         to no children, i.e. an empty directory.
        """
        super().__init__(name)
        self.children = children or {}  # type: Dict[str, Entity]

    def walk_paths(self,
                   base: Optional[pathlib.PurePath] = pathlib.PurePath()) \
            -> Iterator[pathlib.PurePath]:
        yield from itertools.chain.from_iterable(
            [child._walk_paths(base) for child in self.children.values()])

    def _walk_paths(self, base: pathlib.PurePath) \
            -> Iterator[pathlib.PurePath]:
        us = base / self.name
        yield us
        yield from itertools.chain.from_iterable(
            [child.walk_paths(us) for child in self.children.values()])

    def walk_files(self) -> Iterator[File]:
        for child in self.children.values():
            yield from child.walk_files()

    @classmethod
    def from_path(cls, path: pathlib.Path) -> 'Directory':
        """
        Create a directory entity from a directory path.

        :param path: The path of the directory.
        :return: A directory entity instance representing the directory.
        :raises ValueError: If the path does not point to a directory.
        """
        if not path.is_dir():
            raise ValueError('Path does not point to a directory')
        return Directory(path.name, {entity.name: Entity.from_path(entity)
                                     for entity in path.iterdir()})

    def print_hierarchy(self, level: int = 0, file: IO[str] = sys.stdout) \
            -> None:
        print(' ' * self._INDENT_SIZE * level + str(self), file=file)
        for name, child in self.children.items():
            child.print_hierarchy(level + 1, file)


class Root(Directory):
    """
    Represents a nameless directory at the root of a hierarchy. This is useful
    as a substitute for a list of entities representing the contents of the
    root directory.
    """

    def __init__(self, children: Dict[str, Entity]):
        """
        Initialise a root directory.

        :param children: Child entities within this directory. Names correspond
                         to entity names; their values are the entity objects
                         themselves.
        """
        # children is required as an empty root directory isn't very useful
        super().__init__('', children)

    @classmethod
    def from_path(cls, path: pathlib.Path) -> 'Root':
        """
        Create a root directory entity from a directory path.

        :param path: The path of the directory.
        :return: A root directory entity instance representing the directory.
        :raises ValueError: If the path does not point to a directory.
        """
        if not path.is_dir():
            raise ValueError('Path does not point to a directory')
        return Root({entity.name: Entity.from_path(entity)
                     for entity in path.iterdir()})

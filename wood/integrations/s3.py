# -*- coding: utf-8 -*-
from typing import List, Dict, Union, Any, Iterable, Tuple
import pathlib
import logging
import mimetypes

from wood import util
from wood.comparison import Comparison
from wood.entities import Root, Directory, File, Entity
from wood.sync import Syncer as GenericSyncer


logger = logging.getLogger(__name__)


def objects_to_root(objects: List) -> Root:
    """
    Convert a list of s3 ObjectSummaries into a directory tree.

    :param objects: The list of objects, e.g. the result of calling
                    `.objects.all()` on a bucket.
    :return: The tree structure, contained within a root node.
    """

    def _to_tree(objs: Iterable) -> Dict:
        """
        Build a tree structure from a flat list of objects.

        :param objs: The raw iterable of S3 `ObjectSummary`s, as returned by a
                     bucket listing.
        :return: The listing as a nested dictionary where keys are directory
                 and file names. The values of directories will in turn be a
                 dict. The values of keys representing files will be the
                 `ObjectSummary` instance.
        """
        path_tree = {}
        for obj in objs:
            is_dir = obj.key.endswith('/')
            chunks = [chunk for chunk in obj.key.split('/') if chunk]
            chunk_count = len(chunks)
            tmp = path_tree
            for i, chunk in enumerate(chunks):
                is_last_chunk = i == chunk_count - 1

                if is_last_chunk and not is_dir:
                    tmp[chunk] = obj
                else:
                    # must be a directory
                    if chunk not in tmp:
                        # it doesn't exist - create it
                        tmp[chunk] = {}
                    tmp = tmp[chunk]
        return path_tree

    def _to_entity(key: str, value: Union[Dict, Any]) -> Entity:
        """
        Turn a nested dictionary representing an S3 bucket into the correct
        `Entity` object.

        :param key: The name of the entity.
        :param value: If the entity is a directory, the nested dict
                      representing its contents. Otherwise, the `ObjectSummary`
                      instance representing the file.
        :return: The entity representing the entity name and value pair.
        """
        if isinstance(value, dict):
            return Directory(
                key,
                {key_: _to_entity(key_, value_)
                 for key_, value_ in value.items()})

        return File(pathlib.PurePath(value.key).name, value.size,
                    value.e_tag.strip('"'))

    tree = _to_tree(objects)
    return Root({pathlib.PurePath(key).name: _to_entity(key, value)
                 for key, value in tree.items()})


class Syncer(GenericSyncer[Root, Directory]):
    """
    Synchronises a local directory with an S3 bucket.
    """

    # the maximum number of keys that can be specified in a single delete call
    _MAX_DELETES_PER_REQUEST = 1_000

    def __init__(self, base: pathlib.PurePath, bucket, prefix: str = ''):
        """
        Initialise a new S3 syncer.

        :param base: The local base directory.
        :param bucket: The bucket to upload to.
        :param prefix: The prefix within which to work, within the bucket.
                       Defaults to no prefix, i.e. the root of the bucket.
        """
        self._base = base
        self._bucket = bucket
        self._prefix = prefix

    def _delete(self, paths: Iterable[str]) -> None:
        """
        Delete a collection of paths from S3.

        :param paths: The paths to delete. The prefix will be prepended to each
                      one.
        :raises ClientError: If any request fails.
        """
        for chunk in util.chunk(paths, self._MAX_DELETES_PER_REQUEST):
            keys = list([self._prefix + key for key in chunk])
            logger.info('Deleting %d objects (%s)', len(keys), ', '.join(keys))
            response = self._bucket.delete_objects(Delete={
                'Objects': [{'Key': key} for key in keys],
                'Quiet': True
            })
            logger.debug('Delete objects response: %s', response)

    def _upload(self, items: Iterable[Tuple[str, str]]) -> None:
        """
        Upload a collection of paths to S3.

        :param items: An iterable of pairs containing the local path of the
                      file to upload, and the remote path to upload it to. The
                      prefix will be appended to each remote path.
        """
        for src, key in items:
            logger.info(f'Uploading {src} to {key}')
            mimetype, _ = mimetypes.guess_type(src)
            if mimetype is None:
                logger.warning(f'Could not guess MIME type for {src}')
                mimetype = 'application/octet-stream'

            logger.debug(f'Deduced MIME type: {mimetype}')
            self._bucket.upload_file(src, key, ExtraArgs={
                    'ContentType': mimetype
                })

    def sync(self, comparison: Comparison[Root, Directory]) -> None:
        self._delete(comparison.deleted(include_directories=False))
        self._upload(zip(comparison.new(self._base,
                                        include_intermediates=False),
                         comparison.new(include_intermediates=False)))
        self._upload(zip(comparison.modified(self._base),
                         comparison.modified()))

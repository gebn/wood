# -*- coding: utf-8 -*-
import logging
import itertools
from typing import List

import requests
import backoff

from wood import util
from wood.comparison import Comparison
from wood.entities import Entity
from wood.invalidate import Invalidator


logger = logging.getLogger(__name__)


class CloudflareInvalidator(Invalidator):
    """
    Invalidates URLs within a Cloudflare zone.
    """

    _API_BASE = 'https://api.cloudflare.com'
    _MAX_INVALIDATIONS_PER_REQUEST = 30

    def __init__(self, session: requests.Session, email: str, key: str,
                 zone: str, prefix: str):
        """
        Initialise a new Cloudflare cache invalidator.

        :param session: The requests session to use when interacting with
                        Cloudflare.
        :param zone: The zone ID to purge from.
        :param prefix: The full URL prefix to append asset paths to,
                       e.g. https://example.com/webroot/. Should always end
                       with a trailing slash.
        """
        self._session = session
        self._email = email
        self._key = key
        self._zone = zone
        self._prefix = prefix

    def invalidate(self, comparison: Comparison[Entity, Entity]) -> None:
        """
        Invalidate paths in a zone. See https://api.cloudflare.com
        /#zone-purge-individual-files-by-url-and-cache-tags

        :param comparison: The comparison whose changes to invalidate.
        :raises requests.exceptions.RequestException: On request failure.
        :raises RuntimeError: If the request succeeded but could not be carried
                              out.
        """

        @backoff.on_exception(backoff.expo,
                              requests.exceptions.RequestException,
                              max_tries=5,
                              giveup=lambda e:
                              400 <= e.response.status_code < 500)
        def _request(chunk: List[str]) -> requests.Response:
            """
            Send a purge cache request to Cloudflare. This method will
            automatically retry with a back-off in case of server-side error.

            :param chunk: The list of paths to purge. These should not have a
                          leading slash, and will be combined with the prefix
                          to form a URL.
            :return: Cloudflare's response to our successful request.
            :raises requests.exceptions.RequestException: If the request fails
                                                          on the 5th attempt.
            """
            response = self._session.delete(
                '{0._API_BASE}/client/v4/zones/{0._zone}'
                '/purge_cache'.format(self),
                headers={
                    'X-Auth-Email': self._email,
                    'X-Auth-Key': self._key
                },
                json={
                    'files': [self._prefix + path for path in chunk]
                })
            response.raise_for_status()
            return response

        paths = itertools.chain(comparison.deleted(), comparison.modified())
        for chunk_ in util.chunk(paths, self._MAX_INVALIDATIONS_PER_REQUEST):
            chunk_ = list(chunk_)
            if not chunk_:
                # nothing to do
                return
            logger.info('Invalidating %d paths (%s)', len(chunk_),
                        ', '.join(chunk_))
            response_ = _request(chunk_)
            logger.debug('Cloudflare invalidation response [%d]: %s',
                         response_.status_code,
                         response_.text)
            json_ = response_.json()
            if not json_['success']:
                # this would be strange - the API returned a success response
                # code, but success was not "true"
                # TODO more appropriate exception, with handling upstream
                raise RuntimeError('Cloudflare reported failure')
            logger.info('Created invalidation %s', json_['result']['id'])

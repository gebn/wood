# -*- coding: utf-8 -*-
from typing import Iterator, Any
import logging

from wood.invalidate import PrefixInvalidator


logger = logging.getLogger(__name__)


class CloudFrontInvalidator(PrefixInvalidator):
    """
    Invalidates paths in a CloudFront distribution.
    """

    def __init__(self, client: Any, distribution: str, reference: str):
        """
        Initialise a new CloudFront invalidator.

        :param client: The boto3 CloudFront client to use when interacting with
                       the service.
        :param distribution: The distribution ID to invalidate.
        :param reference: A description for any invalidations performed using
                          this instance.
        """
        self._client = client
        self._distribution = distribution
        self._reference = reference

    def _invalidate_prefixes(self, prefixes: Iterator[str]) -> None:
        prefixes = list(['/' + prefix for prefix in prefixes])
        if not prefixes:
            # nothing to do (CloudFront will complain if given an empty list)
            return
        logger.info('Invalidating %d prefixes (%s)', len(prefixes),
                    ', '.join(prefixes))
        response = self._client.create_invalidation(
            DistributionId=self._distribution,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(prefixes),
                    'Items': prefixes
                },
                'CallerReference': self._reference
            })
        logger.debug('CloudFront invalidation response: %s', response)
        logger.info('Created invalidation %s', response['Invalidation']['Id'])

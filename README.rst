wood
====

.. image:: https://travis-ci.org/gebn/wood.svg?branch=master
   :target: https://travis-ci.org/gebn/wood
.. image:: https://coveralls.io/repos/github/gebn/wood/badge.svg?branch=master
   :target: https://coveralls.io/github/gebn/wood?branch=master

Wood is a toolbox for representing directory trees, calculating comparisons
between them, and effecting those changes in S3, CloudFront and Cloudflare. It
started as a set of deploy scripts for my personal website, but grew into
something that I was too chuffed with to keep hidden away in the bowls of
another website repository. It's not as refined as, say, requests, but should
be useful to anyone looking to efficiently deploy a website to AWS, and/or
using Cloudflare as a CDN.

Notably, unlike the AWS CLI tools or boto3, wood does not rely on file
timestamps, instead using MD5 checksums to make the minimum number of changes
possible in S3. It also has an algorithm for aggregating invalidation paths to
make the CloudFront free tier go as far as possible. Syncers and invalidators
are implemented in a generic way, allowing easy extension to additional
services as needed.

Features
--------

- Tree representation
- Tree comparison

  - Action that comparison in S3
  - Invalidate paths as necessary in CloudFront and Cloudflare

Demo
----

.. code-block:: python

    import wood

    # low-level comparison of two local directories
    comparison = wood.compare('~/dir', '~/.snapshot/hourly.1/dir')
    comparison.new()       # files added since the snapshot
    comparison.modified()  # files modified since the snapshot
    comparison.deleted()   # files deleted since the snapshot


    import pathlib
    import boto3

    local_base = pathlib.Path('/path/to/web/root')
    bucket = boto3.resource('s3').Bucket('example.com')

    # create representations of the local and remote trees
    to_deploy = wood.root(local_base)
    deployed = wood.s3.objects_to_root(bucket.objects.all())

    # compare the two as if they were local directories
    comparison = wood.compare(to_deploy, deployed)

    # write all changes (additions, modifications, deletions) to the S3 bucket
    syncer = wood.s3.S3Syncer(local_base, bucket)
    syncer.sync(comparison)

    # invalidate the minimum amount in CloudFront to ensure the changes are
    # visible, using prefix grouping where possible
    cloudfront = boto3.client('cloudfront')
    invalidator = wood.cloudfront.CloudFrontInvalidator(cloudfront,
                                                        '{distribution}',
                                                        '{reference}')
    invalidator.invalidate(comparison)

    # do the same for Cloudflare in the case of a second CDN
    cloudflare = wood.cloudflare.CloudflareInvalidator(
        sess, email, key, zone, 'https://example.com/')
    cloudflare.invalidate(comparison)

Why "wood"?
-----------

Because it started as a tree comparison tool, and grew out from there. It's
also a little rough around the edges.

wood
====

.. image:: https://travis-ci.org/gebn/wood.svg?branch=master
   :target: https://travis-ci.org/gebn/wood
.. image:: https://coveralls.io/repos/github/gebn/wood/badge.svg?branch=master
   :target: https://coveralls.io/github/gebn/wood?branch=master

Wood is a toolbox for representing directory trees, calculating comparisons between them, and effecting those changes in S3, CloudFront and Cloudflare. It started as a set of deploy scripts for my personal website, but grew into something that I was too chuffed with to keep hidden away in the bowls of another website repository. It's not as refined as, say, requests, but should be useful to anyone looking to efficiently deploy a website to AWS, and/or using Cloudflare as a CDN.

Notably, unlike the AWS CLI tools or boto3, wood does not rely on file timestamps, instead using MD5 checksums to make the minimum number of changes possible in S3. It also has an algorithm for aggregating invalidation paths to make the CloudFront free tier go as far as possible. Syncers and invalidators are implemented in a generic way, allowing easy extension to additional services as needed.

Features
--------

- Tree representation
- Tree comparison

  - Action that comparison in S3
  - Invalidate paths as necessary in CloudFront and Cloudflare

Why "wood"?
-----------

Because it started as a tree comparison tool, and grew out from there. It's also a little rough around the edges.

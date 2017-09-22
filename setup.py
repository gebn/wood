# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


def _read_file(name, encoding='utf-8') -> str:
    """
    Read the contents of a file.

    :param name: The name of the file in the current directory.
    :param encoding: The encoding of the file; defaults to utf-8.
    :return: The contents of the file.
    """
    with open(name, encoding=encoding) as f:
        return f.read()


setup(
    name='wood',
    version='1.0.0-rc.2',
    description='Compare directories, efficiently sync changes to AWS, and '
                'invalidate CDNs.',
    long_description=_read_file('README.rst'),
    license='MIT',
    url='https://github.com/gebn/wood',
    author='George Brighton',
    author_email='oss@gebn.co.uk',
    packages=find_packages(),
    zip_safe=True,
    install_requires=[
        'backoff',
        'boto3',
        'botocore',
        'more-itertools',
        'requests'
    ],
    test_suite='nose.collector',
    tests_require=[
        'coverage',
        'coveralls',
        'mock',
        'nose'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

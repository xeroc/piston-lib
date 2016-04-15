#!/usr/bin/env python

from setuptools import setup
from pip.req import parse_requirements

VERSION = '0.1'

setup(name='steem',
      version=VERSION,
      description='Python library for STEEM',
      long_description=open('README.rst').read(),
      download_url='https://github.com/xeroc/python-steem/tarball/' + VERSION,
      author='Fabian Schuh',
      author_email='<Fabian@BitShares.eu>',
      maintainer='Fabian Schuh',
      maintainer_email='<Fabian@BitShares.eu>',
      url='http://www.github.com/xeroc/python-steem',
      keywords=['steem', 'library', 'api', 'rpc'],
      packages=["steemapi", "steembase"],
      classifiers=['License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 3',
                   'Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Financial and Insurance Industry',
                   'Topic :: Office/Business :: Financial',
                   ],
      install_requires=["requests",
                        "websocket-client",
                        ],
      # setup_requires=['pytest-runner'],
      # tests_require=['pytest'],
      )

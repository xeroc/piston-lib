# UNMAINTAINED

This library is unmaintained, do not build productive buisness with it!
Please note the disclaimer in the license file!


Python Library for Steem
========================

Python 3 library for Steem!

**Stable**

[![docs master](https://readthedocs.org/projects/piston-lib/badge/?version=latest)](http://piston-lib.readthedocs.io/en/latest/)
[![Travis master](https://travis-ci.org/xeroc/piston-lib.png?branch=master)](https://travis-ci.org/xeroc/piston-lib)
[![codecov](https://codecov.io/gh/xeroc/piston-lib/branch/master/graph/badge.svg)](https://codecov.io/gh/xeroc/piston-lib)


[![PyPI](https://img.shields.io/pypi/dm/steem.svg?maxAge=2592000)]()
[![PyPI](https://img.shields.io/pypi/dw/steem.svg?maxAge=2592000)]()
[![PyPI](https://img.shields.io/pypi/dd/steem.svg?maxAge=2592000)]()

**Develop**

[![docs develop](https://readthedocs.org/projects/piston-lib/badge/?version=develop)](http://piston-lib.readthedocs.io/en/develop/)
[![Travis develop](https://travis-ci.org/xeroc/piston-lib.png?branch=develop)](https://travis-ci.org/xeroc/piston-lib)
[![codecov develop](https://codecov.io/gh/xeroc/piston-lib/branch/develop/graph/badge.svg)](https://codecov.io/gh/xeroc/piston-lib)

Installation
------------

Install with `pip3`:

    $ sudo apt-get install libffi-dev libssl-dev python-dev python3-pip
    $ pip3 install piston-lib

Manual installation:

    $ git clone https://github.com/xeroc/piston-lib/
    $ cd piston-lib
    $ python3 setup.py install --user

Upgrade
-------

    $ pip3 install steem --user --upgrade

Additional dependencies
-----------------------

`steemapi.steemasyncclient`:
 * `asyncio==3.4.3`
 * `pyyaml==3.11`

Documentation
-------------

Thanks to readthedocs.io, the documentation can be viewed on
[lib.piston.rocks](http://lib.piston.rocks)

Documentation is written with the help of sphinx and can be compile to
html with:

    cd docs
    make html

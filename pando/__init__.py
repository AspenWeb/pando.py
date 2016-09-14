"""
#########
  Pando
#########

This is Pando, a Python web framework.

Pando's source code is on `GitHub`_, and is `MIT-licensed`_.

.. _github: https://github.com/AspenWeb/pando.py
.. _MIT-licensed: http://opensource.org/licenses/MIT


**************
 Installation
**************

:py:mod:`pando` is available on `PyPI`_::

    $ pip install pando

.. _pypi: https://pypi.python.org/pypi/pando


*************
 Quick Start
*************

Given: `POSIX <http://en.wikipedia.org/wiki/POSIX#POSIX-oriented_operating_systems>`_
and `virtualenv <http://pypi.python.org/pypi/virtualenv>`_

Step 1: Make a sandbox::

    $ virtualenv foo
    $ cd foo
    $ . bin/activate

Step 2: Install `pando from PyPI <http://pypi.python.org/pypi/pando>`_::

    (foo)$ pip install pando
    blah
    blah
    blah

Step 3: Create a website root::

    (foo)$ mkdir www
    (foo)$ cd www

Step 4: Create a web page, and start pando inside it::

    (foo)$ echo Greetings, program! > index.html.spt
    (foo)$ pando
    Greetings, program! Welcome to port 8080.

Step 5: Check `localhost <http://localhost:8080>`_ for your new page!

    .. image:: ../doc/quick-start/greetings-program.small.png


***********
 Reference
***********

This is the API reference for the Pando library.

.. automodule:: pando.auth
.. automodule:: pando.body_parsers
.. automodule:: pando.exceptions
.. automodule:: pando.http
.. automodule:: pando.logging
.. automodule:: pando.state_chain
.. automodule:: pando.testing
.. automodule:: pando.utils
.. automodule:: pando.website
.. automodule:: pando.wsgi

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from os.path import dirname, join
import sys
import pkg_resources

import aspen.utils as _x  # this registers the 'repr' codec error strategy
del _x

# imports of convenience
from aspen.simplates import json_ as json
from aspen.simplates.renderers import BUILTIN_RENDERERS, RENDERERS
from .http.response import Response
from .logging import log, log_dammit

# Shut up, PyFlakes. I know I'm addicted to you.
Response, json, log, log_dammit, BUILTIN_RENDERERS, RENDERERS

try:
    dist = pkg_resources.get_distribution('pando')
    __version__ = dist.version
except pkg_resources.DistributionNotFound:
    with open(join(dirname(dirname(__file__)), 'version.txt')) as f:
        __version__ = f.read()

WINDOWS = sys.platform[:3] == 'win'

is_callable = callable


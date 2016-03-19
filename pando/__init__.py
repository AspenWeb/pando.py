"""This is Pando, a Python web framework.


Installation
------------

:py:mod:`pando` is available on `GitHub`_ and on `PyPI`_::

    $ pip install pando

We `test <https://travis-ci.org/gittip/pando-python>`_ against Python 2.7.

:py:mod:`pando` is in `MIT-licensed`_.

.. _github: https://github.com/gittip/pando-python
.. _pypi: https://pypi.python.org/pypi/pando
.. _MIT-licensed: http://opensource.org/licenses/MIT


Quick Start
-----------

Given: `POSIX <http://en.wikipedia.org/wiki/POSIX#POSIX-oriented_operating_systems>`_
and `virtualenv <http://pypi.python.org/pypi/virtualenv>`_

Step 1: Make a sandbox:

    $ virtualenv foo
    $ cd foo
    $ . bin/activate</pre>
    ::

Step 2: Install `pando from PyPI <http://pypi.python.org/pypi/pando>`_:

    (foo)$ pip install pando
    blah
    blah
    blah
    ::

Step 3: Create a website root:

    (foo)$ mkdir www
    (foo)$ cd www</pre>
    ::

Step 4: Create a web page, and start pando inside it:

    (foo)$ echo Greetings, program! > index.html.spt
    (foo)$ pando
    Greetings, program! Welcome to port 8080.
    ::

Step 5: Check `localhost http://localhost:8080`_ for your new page!

    .. image:: greetings-program.png

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import pkg_resources

# imports of convenience
from .http.response import Response
from . import json_ as json
from .logging import log, log_dammit
from .simplates.renderers import BUILTIN_RENDERERS, RENDERERS

# Shut up, PyFlakes. I know I'm addicted to you.
Response, json, log, log_dammit, BUILTIN_RENDERERS, RENDERERS

dist = pkg_resources.get_distribution('pando')
__version__ = dist.version
WINDOWS = sys.platform[:3] == 'win'

is_callable = callable


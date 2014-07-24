"""This is Aspen, a dynamic Jekyll for Python.


Installation
------------

:py:mod:`aspen` is available on `GitHub`_ and on `PyPI`_::

    $ pip install aspen

We `test <https://travis-ci.org/gittip/aspen-python>`_ against Python 2.6 and 2.7.

:py:mod:`aspen` is in `MIT-licensed`_.

.. _github: https://github.com/gittip/aspen-python
.. _pypi: https://pypi.python.org/pypi/aspen
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

Step 2: Install `aspen from PyPI <http://pypi.python.org/pypi/aspen>`_:

    (foo)$ pip install aspen
    blah
    blah
    blah
    ::

Step 3: Create a website root:

    (foo)$ mkdir www
    (foo)$ cd www</pre>
    ::

Step 4: Create a web page, and start aspen inside it:

    (foo)$ echo Greetings, program! > index.html.spt
    (foo)$ aspen
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

from .backcompat import is_callable

# imports of convenience
from aspen.http.response import Response
from aspen import json_ as json
from aspen.logging import log, log_dammit

# Shut up, PyFlakes. I know I'm addicted to you.
Response, json, is_callable, log, log_dammit

dist = pkg_resources.get_distribution('aspen')
__version__ = dist.version
WINDOWS = sys.platform[:3] == 'win'

BUILTIN_RENDERERS = [ 'stdlib_format'
                    , 'stdlib_percent'
                    , 'stdlib_template'
                    , 'json_dump'
                    , 'jsonp_dump'
                     ]

RENDERERS = BUILTIN_RENDERERS[:]

for entrypoint in pkg_resources.iter_entry_points(group='aspen.renderers'):
    RENDERERS.append(entrypoint.name)

RENDERERS.sort()


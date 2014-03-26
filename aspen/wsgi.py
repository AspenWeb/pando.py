"""
aspen.wsgi
++++++++++

Provide a WSGI callable.

It would be a little nicer if this was at aspen:wsgi instead of
aspen.wsgi:website, but then Website would be instantiated even if we don't
want it to be. Here, it's only instantiated when someone passes this to
gunicorn, spawning, etc.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.website import Website

website = Website([])

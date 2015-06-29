"""
python -m aspen
===============

Aspen ships with a server (wsgiref.simple_server) that is
suitable for development and testing.  It can be invoked via:

    python -m aspen

though even for development you'll likely want to specify a
project root, so a more likely incantation is:

    ASPEN_PROJECT_ROOT=/path/to/wherever python -m aspen

For production deployment, you should probably deploy using
a higher performance WSGI server like Gunicorn, uwsgi, Spawning,
or the like.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import serve, website

if __name__ == '__main__':
    serve(website.Website())

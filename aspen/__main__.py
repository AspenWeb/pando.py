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

from aspen.website import Website
from wsgiref.simple_server import make_server



if __name__ == '__main__':
    make_server('0.0.0.0', 8080, Website()).serve_forever()

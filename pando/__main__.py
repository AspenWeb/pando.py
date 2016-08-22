"""
python -m pando
===============

Pando ships with a server (wsgiref.simple_server) that is
suitable for development and testing.  It can be invoked via:

    python -m pando

though even for development you'll likely want to specify a
project root, so a more likely incantation is:

    ASPEN_PROJECT_ROOT=/path/to/wherever python -m pando

For production deployment, you should probably deploy using a higher
performance WSGI server like Gunicorn, uwsgi, Spawning, or the like.

Also, you'll likely want to configure logging your own way, and
pass more configuration options to the Website() constructor.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import logging.config
from wsgiref.simple_server import make_server

from . import  website
from .logging import log_dammit


logging_cfg = {
    'version': 1,
    'formatters': {
        'threadinfo': {
            'format': "%(asctime)s pid-%(process)d thread-%(thread)d (%(threadName)s) %(levelname)s: %(message)s"
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'threadinfo',
            'level': 'INFO',
            'stream': 'ext://sys.stderr'
        }
    },
    'root': {
        'handlers': [ 'console' ]
    }
}


if __name__ == '__main__':
    logging.config.dictConfig(logging_cfg)
    port = int(os.environ.get('PORT', '8080')) # get the port, defaulting to 8080
    host = os.environ.get('PANDO_HOST', '0.0.0.0') # get the IP to bind to, or default to all
    log_dammit("Greetings, program! Now serving on http://{0}:{1}/.".format(host, port))
    website = website.Website()
    make_server(host, port, website).serve_forever()

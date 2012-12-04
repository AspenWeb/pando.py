"""Run the aspen webserver as a FastCGI process.  Requires that you have flup installed.
"""

from aspen.wsgi import website
from flup.server.fcgi import WSGIServer

def main():
    WSGIServer(website).run()


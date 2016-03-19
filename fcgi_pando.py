"""Run the pando webserver as a FastCGI process.  Requires that you have flup installed.
"""

from pando.wsgi import website
from flup.server.fcgi import WSGIServer

def main():
    WSGIServer(website).run()


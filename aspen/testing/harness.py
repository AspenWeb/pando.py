from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
from collections import namedtuple

from aspen import resources, sockets
from aspen.http.request import Request
from aspen.network_engines import ThreadedBuffer
from aspen.sockets.channel import Channel
from aspen.sockets.socket import Socket
from aspen.sockets.transport import XHRPollingTransport
from aspen.testing.client import Client
from filesystem_tree import FilesystemTree


CWD = os.getcwd()


def teardown():
    """Standard teardown function.

    - reset the current working directory
    - remove FSFIX = %{tempdir}/fsfix
    - reset Aspen's global state
    - clear out sys.path_importer_cache
    - clear out execution.extras

    """
    os.chdir(CWD)
    # Reset some process-global caches. Hrm ...
    resources.__cache__ = {}
    sockets.__sockets__ = {}
    sockets.__channels__ = {}
    sys.path_importer_cache = {} # see test_weird.py
    import aspen.execution
    aspen.execution.clear_changes()

teardown() # start clean


class Harness(object):
    """A harness to be used in the Aspen test suite itself. Probably not useful to you.
    """

    def __init__(self):
        self.fs = namedtuple('fs', 'www project')
        self.fs.www = FilesystemTree()
        self.fs.project = FilesystemTree()
        self.client = Client(self.fs.www.root, self.fs.project.root)

    def teardown(self):
        self.fs.www.remove()
        self.fs.project.remove()


    # Simple API
    # ==========

    def simple(self, contents='Greetings, program!', filepath='index.html.spt', uripath=None,
            argv=None, **kw):
        """A helper to create a file and hit it through our machinery.
        """
        if filepath is not None:
            self.fs.www.mk((filepath, contents))
        if argv is not None:
            self.client.hydrate_website(argv)

        if uripath is None:
            if filepath is None:
                uripath = '/'
            else:
                uripath = '/' + filepath
                if uripath.endswith('.spt'):
                    uripath = uripath[:-len('.spt')]
                for indexname in self.client.website.indices:
                    if uripath.endswith(indexname):
                        uripath = uripath[:-len(indexname)]
                        break

        return self.client.GET(uripath, **kw)

    def make_request(self, *a, **kw):
        kw['stop_after'] = 'dispatch_request_to_filesystem'
        kw['want'] = 'request'
        return self.simple(*a, **kw)


    # Sockets
    # =======

    def make_transport(self, content='', state=0):
        self.fs.www.mk(('echo.sock.spt', content))
        socket = self.make_socket()
        transport = XHRPollingTransport(socket)
        transport.timeout = 0.05 # for testing, could screw up the test
        if state == 1:
            transport.respond(Request(uri='/echo.sock'))
        return transport

    def make_socket_request(self, filename='echo.sock.spt'):
        request = Request(uri='/echo.sock')
        request.website = self.client.website
        request.fs = self.fs.www.resolve(filename)
        return request

    def make_socket(self, filename='echo.sock.spt', channel=None):
        request = self.make_socket_request(filename='echo.sock.spt')
        if channel is None:
            channel = Channel(request.line.uri.path.raw, ThreadedBuffer)
        socket = Socket(request, channel)
        return socket

    def SocketInThread(harness):

        class _SocketInThread(object):

            def __enter__(self, filename='echo.sock.spt'):
                self.socket = harness.make_socket(filename)
                self.socket.loop.start()
                return self.socket

            def __exit__(self, *a):
                self.socket.loop.stop()

        return _SocketInThread()

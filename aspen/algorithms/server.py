from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import os
import signal
import socket
import sys
import traceback

import aspen
from aspen import execution
from aspen.website import Website


def install_handler_for_SIGHUP():
    """
    """
    def SIGHUP(signum, frame):
        aspen.log_dammit("Received HUP, re-executing.")
        execution.execute()
    if not aspen.WINDOWS:
        signal.signal(signal.SIGHUP, SIGHUP)


def install_handler_for_SIGINT():
    """
    """
    def SIGINT(signum, frame):
        aspen.log_dammit("Received INT, exiting.")
        raise SystemExit
    signal.signal(signal.SIGINT, SIGINT)


def install_handler_for_SIGQUIT():
    """
    """
    def SIGQUIT(signum, frame):
        aspen.log_dammit("Received QUIT, exiting.")
        raise SystemExit
    if not aspen.WINDOWS:
        signal.signal(signal.SIGQUIT, SIGQUIT)


def get_website_from_argv(argv, algorithm):
    """

    User-developers get this website object inside of their resources and
    hooks. It provides access to configuration information in addition to being
    a WSGI callable and holding the request/response handling logic. See
    aspen/website.py

    """
    if argv is None:
        argv = sys.argv[1:]
    website = Website(argv, server_algorithm=algorithm)
    return {'website': website}


def bind_server_to_port(website):
    """
    """
    if hasattr(socket, 'AF_UNIX'):
        if website.network_sockfam == socket.AF_UNIX:
            if os.path.exists(website.network_address):
                aspen.log("Removing stale socket.")
                os.remove(website.network_address)
    if website.network_port is not None:
        welcome = "port %d" % website.network_port
    else:
        welcome = website.network_address
    aspen.log("Starting %s engine." % website.network_engine.name)
    website.network_engine.bind()
    aspen.log_dammit("Greetings, program! Welcome to %s." % welcome)


def install_restarter_for_website(website):
    """
    """
    if website.changes_reload:
        aspen.log("Aspen will restart when configuration scripts or "
                  "Python modules change.")
        execution.install(website)


def start(website):
    """
    """
    aspen.log_dammit("Starting up Aspen website.")
    website.network_engine.start()


def stub_website_for_exception(exception, state):
    """
    """
    # Without this, the call to stop fails if we had an exception during configuration.
    if 'website' not in state:
        return {'website': None}


def handle_conflict_over_port(exception, website):
    """Be friendly about port conflicts.

    The traceback one gets from a port conflict or permission error is not that
    friendly. Here's a helper to let the user know (in color?!) that a port
    conflict or a permission error is probably the problem. But in case it
    isn't (website.start fires the start hook, and maybe the user tries to
    connect to a network service in there?), don't fully swallow the exception.
    Also, be explicit about the port number. What if they have logging turned
    off? Then they won't see the port number in the "Greetings, program!" line.
    They definitely won't see it if using an engine like eventlet that binds to
    the port early.

    """
    if exception.__class__ is not socket.error:
        return

    if website.network_port is not None:
        msg = "Is something already running on port %s? Because ..."
        if not aspen.WINDOWS:
            if website.network_port < 1024:
                if os.geteuid() > 0:
                    msg = ("Do you have permission to bind to port %s?"
                           " Because ...")
        msg %= website.network_port
        if not aspen.WINDOWS:
            # Assume we can use ANSI color escapes if not on Windows.
            # XXX Maybe a bad assumption if this is going into a log
            # file? See also: colorama
            msg = '\033[01;33m%s\033[00m' % msg
        aspen.log_dammit(msg)
    raise


def log_traceback_for_exception(exception):
    """
    """
    if exception.__class__ not in (KeyboardInterrupt, SystemExit):
        aspen.log_dammit(traceback.format_exc())
    return {'exception': None}


def stop(website):
    """Stop the server.
    """
    if website is None:
        return

    aspen.log_dammit("Shutting down Aspen website.")
    website.network_engine.stop()
    if hasattr(socket, 'AF_UNIX'):
        if website.network_sockfam == socket.AF_UNIX:
            if os.path.exists(website.network_address):
                os.remove(website.network_address)

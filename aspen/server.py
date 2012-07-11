def _main(argv):

    # Do imports.
    # ===========
    # These are in here so that if you Ctrl-C during an import, the
    # KeyboardInterrupt is caught and ignored. Yes, that's how much I care.
    # No, I don't care enough to put aspen/__init__.py in here too.

    import os
    import signal
    import socket
    import sys
    import traceback

    import aspen
    from aspen import execution
    from aspen.website import Website


    # Set up signal handling.
    # =======================

    def SIGHUP(signum, frame):
        aspen.log_dammit("Received HUP, re-executing.")
        execution.execute()
    if not aspen.WINDOWS:
        signal.signal(signal.SIGHUP, SIGHUP)

    def SIGINT(signum, frame):
        aspen.log_dammit("Received INT, exiting.")
        raise SystemExit
    signal.signal(signal.SIGINT, SIGINT)


    def SIGQUIT(signum, frame):
        aspen.log_dammit("Received QUIT, exiting.")
        raise SystemExit
    if not aspen.WINDOWS:
        signal.signal(signal.SIGQUIT, SIGQUIT)


    # Website
    # =======
    # User-developers get this website object inside of their resources and
    # hooks. It provides access to configuration information in addition to
    # being a WSGI callable and holding the request/response handling
    # logic. See aspen/website.py

    if argv is None:
        argv = sys.argv[1:]
    website = Website(argv)


    # Start serving the website.
    # ==========================
    # This amounts to binding the requested socket, with logging and
    # restarting as needed. Wrap the whole thing in a try/except to
    # do some cleanup on shutdown.

    try:
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
        if website.changes_reload:
            aspen.log("Aspen will restart when configuration scripts or "
                      "Python modules change.")
            execution.install(website)
        website.start()

    except socket.error:

        # Be friendly about port conflicts.
        # =================================

        # The traceback one gets from a port conflict or permission error
        # is not that friendly. Here's a helper to let the user know (in
        # color?!) that a port conflict or a permission error is probably
        # the problem. But in case it isn't (website.start fires the start
        # hook, and maybe the user tries to connect to a network service in
        # there?), don't fully swallow the exception. Also, be explicit
        # about the port number. What if they have logging turned off? Then
        # they won't see the port number in the "Greetings, program!" line.
        # They definitely won't see it if using an engine like eventlet
        # that binds to the port early.

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
    except (KeyboardInterrupt, SystemExit):
        raise  # Don't bother logging these.
    except:
        aspen.log_dammit(traceback.format_exc())
    finally:
        if hasattr(socket, 'AF_UNIX'):
            if website.network_sockfam == socket.AF_UNIX:
                if os.path.exists(website.network_address):
                    os.remove(website.network_address)
        website.stop()

def main(argv=None):
    """http://aspen.io/cli/
    """
    try:
        _main(argv)
    except SystemExit:
        pass
    except:
        import aspen, aspen.execution, time, traceback
        aspen.log_dammit("Oh no! Aspen crashed!")
        aspen.log_dammit(traceback.format_exc())
        try:
            while 1:
                aspen.execution.check_all()
                time.sleep(1)
        except KeyboardInterrupt:
            raise SystemExit

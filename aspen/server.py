def main(argv=None):
    """http://aspen.io/cli/
    """
    try:

        # Do imports.
        # ===========
        # These are in here so that if you Ctrl-C during an import, the
        # KeyboardInterrupt is caught and ignored. Yes, that's how much I care.
        # No, I don't care enough to put aspen/__init__.py in here too.

        import os
        import logging
        import socket
        import sys
        import time
        import traceback
        from os.path import exists, join

        import aspen
        from aspen import restarter
        from aspen.website import Website

        
        log = logging.getLogger('aspen.cli')


        # Website
        # =======
        # User-developers get this website object inside of their simplates and
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
                if website.sockfam == socket.AF_UNIX:
                    if exists(website.address):
                        log.info("Removing stale socket.")
                        os.remove(website.address)
            if website.port is not None:
                welcome = "port %d" % website.port
            else:
                welcome = website.address
            log.info("Starting %s engine." % website.engine.name)
            website.engine.bind()
            log.warn("Greetings, program! Welcome to %s." % welcome)
            if website.changes_kill:
                log.info("Aspen will die when files change.")
                restarter.install(website)
            website.start()

        except socket.error:

            # Be friendly about port conflicts.
            # =================================
            # The traceback one gets from a port conflict is not that friendly.
            # Here's a helper to let the user know (in color?!) that a port
            # conflict is the probably the problem. But in case it isn't
            # (website.start fires the start hook, and maybe the user tries to
            # connect to a network service in there?), don't fully swallow the
            # exception. Also, be explicit about the port number. What if they
            # have logging turned off? Then they won't see the port number in
            # the "Greetings, program!" line. They definitely won't see it if
            # using an engine like eventlet that binds to the port early.

            if website.port is not None:
                msg = "Is something already running on port %s? Because ..."
                msg %= website.port
                if not aspen.WINDOWS:
                    # Assume we can use ANSI color escapes if not on Windows.
                    # XXX Maybe a bad assumption if this is going into a log 
                    # file?
                    msg = '\033[01;33m%s\033[00m' % msg
                print >> sys.stderr, msg
            raise

        except KeyboardInterrupt, SystemExit:
            pass
        except:
            traceback.print_exc()
        finally:
            if hasattr(socket, 'AF_UNIX'):
                if website.sockfam == socket.AF_UNIX:
                    if exists(website.address):
                        os.remove(website.address)
            website.stop()
    except KeyboardInterrupt, SystemExit:
        pass


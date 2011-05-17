def main(argv=None):
    """http://aspen.io/cli/
    """
    try:

        # Do imports.
        # ===========
        # These are in here so that if you Ctrl-C during an import, the
        # Keyboard Interupt is caught and ignored. Yes, that's how much I care.
        # No, I don't care enough to put aspen/__init__.py in here too.

        import os
        import logging
        import socket
        import sys
        import time
        from os.path import exists, join

        try:
            import eventlet
            import eventlet.wsgi
        except ImportError:
            print >> sys.stderr, ("You need to install eventlet in order to "
                                  "run aspen.")
            raise SystemExit

        from aspen.cli import restarter
        from aspen.website import Website


        log = logging.getLogger('aspen.cli')


        class DevNull:
            def write(self, msg):
                pass


        # Actual stuff.
        # =============

        if argv is None:
            argv = sys.argv[1:]
        website = Website(argv)
        try:
            if website.sockfam == socket.AF_UNIX:
                if exists(website.address):
                    log.warn("Removing stale socket.")
                    os.remove(website.address)
            sock = eventlet.listen(website.address, website.sockfam)
            if website.port is not None:
                welcome = "port %d" % website.port
            else:
                welcome = website.address
            restarter.install(website)
            log.warn("Greetings, program! Welcome to %s." % welcome)
            eventlet.wsgi.server(sock, website, log=DevNull())
        finally:
            if website.sockfam == socket.AF_UNIX:
                if exists(website.address):
                    os.remove(website.address)
            website.shutdown()
    except KeyboardInterrupt, SystemExit:
        pass


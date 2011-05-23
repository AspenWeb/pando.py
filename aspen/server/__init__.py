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

        from aspen.server import restarter
        from aspen.website import Website

        
        log = logging.getLogger('aspen.cli')


        # Actual stuff.
        # =============

        if argv is None:
            argv = sys.argv[1:]
        website = Website(argv)
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
            log.warn("Greetings, program! Welcome to %s." % welcome)
            if website.changes_kill:
                restarter.install(website)
            website.engine.start(website)
        finally:
            if hasattr(socket, 'AF_UNIX'):
                if website.sockfam == socket.AF_UNIX:
                    if exists(website.address):
                        os.remove(website.address)
            website.shutdown()
            website.engine.stop()
    except KeyboardInterrupt, SystemExit:
        pass


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


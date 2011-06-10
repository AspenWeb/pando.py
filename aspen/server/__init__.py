class BaseEngine(object):

    def __init__(self, name, website):
        """Takes an identifying string and a WSGI application.
        """
        self.name = name
        self.website = website

    def bind(self):
        """Bind to a socket, based on website.sockfam and website.address.
        """

    def start(self):
        """Start listening on the socket.
        """

    def stop(self):
        """Stop listening on the socket.
        """

    def start_restarter(self, check_all):
        """Start a loop that runs check_all every half-second.
        """

    def stop_restarter(self):
        """Stop the loop that runs check_all (optional).
        """


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


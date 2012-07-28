"""Oh, wow.
"""
import time

import twisted.internet
import twisted.internet.task
import twisted.web.server
import twisted.web.wsgi
from aspen.network_engines import ThreadedEngine


class Engine(ThreadedEngine):
    """For v1 we're just running a threaded server. Maybe some day ...
    """

    twisted_site = None

    def bind(self):
        pool = twisted.internet.reactor.getThreadPool()
        resource = twisted.web.wsgi.WSGIResource( twisted.internet.reactor
                                                , pool
                                                , self.website
                                                 )
        self.twisted_site = twisted.web.server.Site(resource)

    def sleep(self, seconds):
        time.sleep(seconds) # We're threaded.

    def start(self):
        twisted.internet.reactor.listenTCP( port=self.website.network_address[1]
                                          , factory=self.twisted_site
                                          , interface=self.website.network_address[0]
                                           )
        twisted.internet.reactor.run()

    def start_checking(self, check_all):
        self.checker = twisted.internet.task.LoopingCall(check_all)
        deferred = self.checker.start(0.5)

        # Set up twisted error handling.
        # ==============================
        # Twisted captures all exceptions, including SystemExit. Glyph actually
        # just told me a story (PyCon 2012 sprints) that when he was a kid his
        # father told him that programs should be robust in the face of error
        # conditions. "If you shoot it in the leg, it should crawl towards you.
        # Then when you crush its torso, it should drag itself towards you.
        # And when you shoot it in the head, it should reach out for you with
        # its dying breath." So he captures SystemExit, and now, due to a very
        # wonderful time together, I can respect that. And that's the way it
        # works, motherfuckers. Get to it!
        #
        # Other memorable quotes:
        #
        # "Twisted started as a MUD written in Java that used three or four
        #  threads per connection."
        # "That was the big moment: if NetHack can do it, so can I!"
        # "No, this wasn't ncurses, this was a full-on Swing app."
        # "1999."
        # "We had this cockroach autonomous character that would go around and
        #  infest your character's possessions, and everyone ended up with,
        #  like, five of these things in their stuff."
        # "I just want there to be a single Python networking library with a
        #  consistent API."
        # "Oh! That's your vim. I thought for a second that Aspen was the most
        #  advanced web server in the world."
        # "I started using vim when I was six."

        def error(failure):
            failure.trap(SystemExit)
            if failure.type is SystemExit and self.checker.running:
                self.checker.stop()

        deferred.addErrback(error)

    def stop_checking(self):
        self.checker.stop()

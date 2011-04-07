import os
import logging
import sys
import time
from os.path import isdir, join

from aspen import restarter
from aspen.website import Website
from aspen.configuration import Configuration
from diesel import Application, Loop, Service
from diesel.protocols import http


log = logging.getLogger('aspen.cli')


def main(argv=None):
    try:
        configuration = Configuration(argv)
        configuration.app = app = Application()
        website = Website(configuration)
        configuration.website = website # to support re-handling, especially
        website = configuration.hooks.run('startup', website)

        # change current working directory
        os.chdir(configuration.root)

        if configuration.conf.aspen.yes('changes_kill'):
            # restart for template files too;
            # TODO generalize this to all of .aspen?
            # TODO can't we just invalidate the simplate cache for these?
            dot_aspen = join(configuration.root, '.aspen')
            for root, dirs, files in os.walk(dot_aspen):
                for filename in files:
                    restarter.add(join(root, filename))

            app.add_loop(Loop(restarter.loop))
        
        port = configuration.address[1]
        app.add_service(Service(http.HttpServer(website), port))

        log.warn("Greetings, program! Welcome to port %d." % port)
        app.run()

    except KeyboardInterrupt, SystemExit:
        configuration.hooks.run('shutdown', website)


def thrash():
    """This is a very simple tool to restart a process when it dies.

    It's designed to restart aspen in development when it dies because files
    have changed and you set changes_kill in the [aspen] section of aspen.conf.

    """
    try:
        while 1:
            os.system(' '.join(sys.argv[1:]))
            time.sleep(1)
    except KeyboardInterrupt:
        pass

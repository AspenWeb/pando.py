import os
import logging
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
        for hook in configuration.hooks.startup:
            website = hook(website) or website

        # change current working directory
        os.chdir(configuration.root)

        # restart for template files too; TODO generalize this to all of etc?
        template_dir = join(configuration.root, '.aspen', 'etc', 'templates')
        if isdir(template_dir):
            for filename in os.listdir(template_dir):
                restarter.add(join(template_dir, filename))
        
        port = configuration.address[1]
        if configuration.conf.aspen.yes('die_when_changed'):
            app.add_loop(Loop(restarter.loop))
        app.add_service(Service(http.HttpServer(website), port))

        log.warn("Greetings, program! Welcome to port %d." % port)
        app.run()

    except KeyboardInterrupt, SystemExit:
        for hook in configuration.hooks.shutdown:
            website = hook(website) or website


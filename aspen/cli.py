import os
import logging
from os.path import isdir, join

from aspen import mode, restarter
from aspen.website import Website
from aspen.configuration import Configuration
from diesel import Application, Loop, Service
from diesel.protocols import http


log = logging.getLogger('aspen.cli')


def main(argv=None):
    configuration = Configuration(argv)
    configuration.app = app = Application()
    website = Website(configuration)

    # change current working directory
    os.chdir(configuration.root)

    # restart for template files too; TODO generalize this to all of etc?
    template_dir = join(configuration.root, '.aspen', 'etc', 'templates')
    if isdir(template_dir):
        for filename in os.listdir(template_dir):
            restarter.add(join(template_dir, filename))
    
    port = configuration.address[1]
    if mode.DEVDEB:
        app.add_loop(Loop(restarter.loop))
    app.add_service(Service(http.HttpServer(website), port))

    log.warn("Greetings, program! Welcome to port %d." % port)
    app.run()


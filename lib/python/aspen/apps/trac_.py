"""Serve a given directory as a Trac environment.

Requires that trac (and dependencies) be installed.

TODO:

    - add a knob in aspen.conf for PYTHON_EGG_CACHE, and set that in os.environ
      here if it is set there. See:

        http://code.google.com/p/modwsgi/wiki/IntegrationWithTrac


"""
import aspen
from trac.web.main import dispatch_request


ROOT = aspen.paths.root

def env(environ, start_response):
    """
    """
    environ['trac.env_path'] = ROOT + environ['SCRIPT_NAME']
    return dispatch_request(environ, start_response)

wsgi = env # default is to serve a single environment


def env_parent_dir(environ, start_response):
    """Serve the directory as a TRAC_ENV_PARENT_DIR
    """
    environ['trac.env_parent_dir'] = ROOT + environ['SCRIPT_NAME']
    return dispatch_request(environ, start_response)

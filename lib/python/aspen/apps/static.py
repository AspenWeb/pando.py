from aspen import configuration
from aspen.handlers.static import wsgi as static_handler
from aspen.utils import find_default, translate


def wsgi(environ, start_response):
    """This makes the static handler available as a full-blown application.
    """
    fspath = translate(environ['PATH_TRANSLATED'], environ['PATH_INFO'])
    fspath = find_default(configuration.defaults, fspath)
    environ['PATH_TRANSLATED'] = fspath
    return static_handler(environ, start_response)

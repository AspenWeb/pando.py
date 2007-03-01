from aspen import configuration
from aspen.handlers.static import static as static_handler
from aspen.utils import find_default, translate


def static(environ, start_response):
    """This makes the static handler available as a full-blown application.
    """
    environ['PATH_TRANSLATED'] = translate( environ['PATH_TRANSLATED']
                                          , environ['PATH_INFO']
                                           )
    fspath = find_default(configuration.defaults, environ)
    environ['PATH_TRANSLATED'] = fspath
    return static_handler(environ, start_response)

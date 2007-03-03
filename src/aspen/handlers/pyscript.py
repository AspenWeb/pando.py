"""Define a handler that interprets files as Python scripts.
"""
from os.path import isfile


def wsgi(environ, start_response):
    """Execute the script pseudo-CGI-style.
    """
    path = environ['PATH_TRANSLATED']
    assert isfile(path) # sanity check

    context = dict()
    context['environ'] = environ
    context['start_response'] = start_response

    try:
        exec open(path) in context
    except SystemExit:
        pass

    if 'response' not in context:
        raise LookupError("script %s does not define 'response'" % path)
    return context['response']

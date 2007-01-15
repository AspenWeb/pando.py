"""Define a handler that interprets files as Python scripts.
"""
from os.path import isfile


def pyscript(environ, start_response):
    """Execute the script pseudo-CGI-style.
    """
    path = environ['PATH_TRANSLATED']
    assert isfile(path) # sanity check

    context = dict()
    context['environ'] = environ
    context['start_response'] = start_response
    context['response'] = []
    context['__file__'] = path

    try:
        exec open(path) in context
        response = context['response']
    except SystemExit:
        pass

    return response

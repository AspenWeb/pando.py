import inspect
import os
import string
import urllib
from os.path import isdir, isfile, join, realpath

from aspen.httpy import Response


INITIAL = '_' + string.letters
INNER = INITIAL + string.digits
def is_valid_identifier(s):
    """Given a string of length > 0, return a boolean.

        >>> is_valid_identifier('.svn')
        False
        >>> is_valid_identifier('svn')
        True
        >>> is_valid_identifier('_svn')
        True
        >>> is_valid_identifier('__svn')
        True
        >>> is_valid_identifier('123')
        False
        >>> is_valid_identifier('r123')
        True

    """
    try:
        assert s[0] in INITIAL
        assert False not in [x in INNER for x in s]
        return True
    except AssertionError:
        return False


def _is_callable_instance(o):
    return hasattr(o, '__class__') and hasattr(o, '__call__')

def cmp_routines(f1, f2):
    """Given two callables, return a boolean. Used in testing.
    """
    try:
        if inspect.isclass(f1):
            assert inspect.isclass(f2)
            assert f1 == f2
        elif inspect.ismethod(f1):
            assert inspect.ismethod(f2)
            assert f1.im_class == f2.im_class
        elif inspect.isfunction(f1):
            assert inspect.isfunction(f2)
            assert f1 == f2
        elif _is_callable_instance(f1):
            assert _is_callable_instance(f2)
            assert f1.__class__ == f2.__class__
        else:
            raise AssertionError("These aren't routines.")
        return True
    except AssertionError:
        return False


# Paths
# =====

def check_trailing_slash(environ):
    """Given a WSGI environ, return None or raise 301.

    environ must have PATH_TRANSLATED set in addition to PATH_INFO, which
    latter is required by the spec.

    """
    fs = environ['PATH_TRANSLATED']
    url = environ['PATH_INFO']
    if isdir(fs) and not url.endswith('/'):
        environ['PATH_INFO'] += '/'
        response = Response(301)
        response.headers['Location'] = full_url(environ)
        raise response


def find_default(defaults, path):
    """Given a list of defaults and a path, return a filepath or raise 403.

    If the path isn't a directory, simply return it.

    """
    default = None
    if isdir(path):
        for name in defaults:
            _path = join(path, name)
            if isfile(_path):
                default = _path
                break
        if default is None:
            raise Response(403)
        path = default
    return path


def full_url(environ):
    """Given a WSGI environ, return the full URL of the request.

    This is Ian's recipe from PEP 333.

    """
    url = environ['wsgi.url_scheme']+'://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME']

        if environ['wsgi.url_scheme'] == 'https':
            if environ['SERVER_PORT'] != '443':
               url += ':' + environ['SERVER_PORT']
        else:
            if environ['SERVER_PORT'] != '80':
               url += ':' + environ['SERVER_PORT']

    url += urllib.quote(environ.get('SCRIPT_NAME',''))
    url += urllib.quote(environ.get('PATH_INFO',''))
    if environ.get('QUERY_STRING'):
        url += '?' + environ['QUERY_STRING']

    return url


def translate(root, url):
    """Translate a URL to the filesystem.
    """
    parts = [root] + url.lstrip('/').split('/')
    return realpath(os.sep.join(parts))


if __name__ == '__main__':
    import doctest
    doctest.testmod()



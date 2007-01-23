import inspect
import os
import string
import urllib
from os.path import isdir, isfile, join, realpath


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

def check_trailing_slash(environ, start_response):
    """Given WSGI stuff, return None or 301.

    environ must have PATH_TRANSLATED set in addition to PATH_INFO, which
    latter is required by the spec.

    """
    fs = environ['PATH_TRANSLATED']
    url = environ['PATH_INFO']
    if isdir(fs) and not url.endswith('/'):
        environ['PATH_INFO'] += '/'
        new_url = full_url(environ)
        start_response( '301 Moved Permanently'
                      , [('Location', new_url)]
                       )
        return ['Resource moved to: ' + new_url]


def full_url(environ):
    """Given a WSGI environ, return the full URL of the request.

    Adapted from Ian Bicking's recipe in PEP 333.

    """

    # Start building the URL.
    # =======================
    # http://

    url = [environ['wsgi.url_scheme'], '://']


    # Get the host.
    # =============
    # http://example.com

    port = None
    if environ.get('HTTP_X_FORWARDED_HOST'):    # try X-Forwarded-Host header
        host = environ['HTTP_X_FORWARDED_HOST']
    elif environ.get('HTTP_HOST'):              # then try Host header
        host = environ['HTTP_HOST']
    else:                                       # fall back to SERVER_NAME
        host = environ['SERVER_NAME']
        port = environ['SERVER_PORT']


    # Get the port.
    # =============
    # http://example.com:8080

    if port is None: # i.e., using X-Forwarded-Host or Host
        if ':' in host:
            assert host.count(':') == 1 # sanity check
            host, port = host.split(':')
        else:
            port = (environ['wsgi.url_scheme'] == 'http') and '80' or '443'


    # Add host and port to the url.
    # =============================

    url.append(host)
    if environ['wsgi.url_scheme'] == 'https':
        if port != '443':
           url.extend([':', port])
    else:
        assert environ['wsgi.url_scheme'] == 'http' # sanity check
        if port != '80':
           url.extend([':', port])


    # Add any path info and querystring.
    # ==================================
    # http://example.com:8080/foo/bar?baz=buz

    script_name = urllib.quote(environ.get('SCRIPT_NAME', ''))
    path_info = urllib.quote(environ.get('PATH_INFO', ''))
    if script_name == path_info == '':
        url.append('/')
    else:
        url.extend([script_name, path_info])
    if environ.get('QUERY_STRING'):
        url.extend(['?', environ['QUERY_STRING']])


    # Put it all together.
    # ====================

    return ''.join(url)


def translate(root, url):
    """Translate a URL to the filesystem.
    """
    parts = [root] + url.lstrip('/').split('/')
    return realpath(os.sep.join(parts))


def find_default(defaults, environ):
    """Given a WSGI environ and a list of defaults, update environ.

    This function updates environ['PATH_TRANSLATED'] and returns the new
    filesystem path, or the old one if no default is found.

    """
    fspath = environ['PATH_TRANSLATED']
    if isdir(fspath):
        default = None
        for name in defaults:
            _path = join(fspath, name)
            if isfile(_path):
                default = _path
                break
        if default is not None:
            environ['PATH_TRANSLATED'] = fspath = default
    return fspath


if __name__ == '__main__':
    import doctest
    doctest.testmod()

"""HACK.

These are here so simplates can be used standalone with Google App Engine.
These duplicate the functions in aspen.utils.  If/when Aspen is refactored
(branches/whit537-too-much) these could go in the pubs dir somewhere and
wouldn't be duplicated.

"""
import os
from os.path import isdir, join, isfile


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


def find_default(defaults, fspath):
    """Given a list of defaults and a filesystem path, return a filesystem path.

    This function returns the new filesystem path, or the old one if no default
    is found.

    """
    if isdir(fspath):
        default = None
        for name in defaults:
            _path = join(fspath, name)
            if isfile(_path):
                default = _path
                break
        if default is not None:
            fspath = default
    return fspath


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

    We specifically avoid removing symlinks in the path so that the filepath
    remains under the website root. Also, we don't want trailing slashes for
    directories.

    """
    parts = [root] + url.lstrip('/').split('/')
    return os.sep.join(parts).rstrip(os.sep)



import StringIO

import aspen
from aspen._configuration import ConfFile, Configuration 
from aspen.tests import assert_raises, configure_logging
from aspen.tests.fsfix import mk, attach_teardown
from aspen.website import Website
from aspen.server import Server
from aspen.load import Handler


configure_logging()


# Fixture
# =======

def simple_rule(fp, pred):
    return True

def simple_wsgi(environ, start_response):
    start_response('200 OK', [])
    return ["You hit %s." % environ.get('HTTP_HOST', '_______')]

simple_handler = Handler(rules={'foo':simple_rule}, handle=simple_wsgi)
simple_handler.add("foo", 0)


class TestWebsite(Website):

    def __init__(self):
        configuration = aspen.configure(['--root', 'fsfix'])
        server = Server(configuration)
        Website.__init__(self, server)

        # sanity checks
        assert getattr(Website, 'start_response', None) is None
        assert getattr(Website, 'check', None) is None

    def start_response(self, status, headers, exc=None):
        def write():
            return status, headers
        return write

    def check(self, path, *returns, **environ):
        """Self.__call__ returns a list of strings (so far); hence *returns.
        """
        environ.update({'PATH_INFO':path})
        returned = self(environ, self.start_response)
        if isinstance(returns[0], StringIO.StringIO):
            assert isinstance(returned, file)
            expected = returns[0].read()
            actual = returned.read()
        else:
            assert isinstance(returned, list)
            expected = list(returns)
            actual = returned
        assert actual == expected, actual

environ_for_trailing_slash = dict()
environ_for_trailing_slash['wsgi.url_scheme'] = 'http'
environ_for_trailing_slash['SERVER_NAME'] = 'bar'
environ_for_trailing_slash['SERVER_PORT'] = '8080'


# Tests
# =====

def test_basic():
    mk()
    website = TestWebsite()
    website.check('/', '<html><head><title>/</title>', '<style>\nbody {font-family: "Trebuchet MS", sans-serif;}\ntable {font-family: monospace;}\n.dir {font-weight: bold;}\n.file {}\ntd {padding: 0 1em 0 0; white-space: nowrap;}\ntd.size {text-align: right;}\nth {text-align: left; white-space: nowrap;}\ntr.even {background: #eee;}\ntr:hover {background: #eef;}\n#footer {font-size: smaller; font-style: italic;}\n\n</style></head><body>\r\n', '<h1>/</h1>\r\n', '<table>\r\n', '<tr><th class="name">Name</th><th>Size</th><th>Last Modified</th></tr>\r\n', '</table>\r\n', '<hr /><div id="footer">This index was brought to you by\r\n', '<a href="http://www.zetadev.com/software/aspen/">\r\n', 'Aspen v~~VERSION~~</a>.</div>\r\n', '</body></html>\r\n')


def test_hides_magic_dir():
    mk(('__/foo', "bar"))
    website = TestWebsite()
    website.check('/__/foo', 'Resource not found.')

def test_hides_README_aspen():
    mk(('README.aspen', "foo"))
    website = TestWebsite()
    website.check('/README.aspen', 'Resource not found.')


def test_app_basic():
    mk('/foo/')
    website = TestWebsite()
    website.server.configuration.apps = [('/foo/', simple_wsgi)]
    website.check('/foo/', 'You hit _______.')

def test_app_no_slash():
    mk('/foo')
    website = TestWebsite()
    website.server.configuration.apps = [('/foo', simple_wsgi)]
    website.check('/foo/', 'You hit _______.')

def test_app_no_dir():
    mk()
    website = TestWebsite()
    website.server.configuration.apps = [('/foo/', simple_wsgi)]
    website.check('/foo/', 'Resource not found.')

def test_app_slash_redirected():
    """check app redirection; should only work when the directory exists
    """
    def check(returns, *m):
        mk(*m)
        website = TestWebsite()
        website.server.configuration.apps = [('/foo/', simple_wsgi)]
        environ = dict(environ_for_trailing_slash)
        website.check('/foo', returns, **environ)
    
    yield check, 'Resource not found.'
    yield check, 'Resource moved to: http://bar:8080/foo/', 'foo'


def test_handler_basic():
    mk()
    website = TestWebsite()
    website.server.configuration.handlers = [simple_handler]
    website.check('/', 'You hit _______.')

def test_handler_not_found():
    mk()
    website = TestWebsite()
    website.server.configuration.handlers = [simple_handler]
    website.check('/foo.html', 'Resource not found.')

def test_handler_slash_redirection():
    mk('/foo/')
    website = TestWebsite()
    environ = dict(environ_for_trailing_slash)
    website.check('/foo', 'Resource moved to: http://bar:8080/foo/', **environ)

def test_handler_default():
    mk(('/foo/index.html', "bar"))
    website = TestWebsite()
    returns = StringIO.StringIO("bar")
    website.check('/foo/', returns)


attach_teardown(globals())

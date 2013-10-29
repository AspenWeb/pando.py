from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple
from Cookie import SimpleCookie
from StringIO import StringIO


from aspen.website import Website


BOUNDARY = 'BoUnDaRyStRiNg'
MULTIPART_CONTENT = 'multipart/form-data; boundary=%s' % BOUNDARY


def encode_multipart(boundary, data):
    """
    Encodes multipart POST data from a dictionary of form values.

    Borrowed from Django
    The key will be used as the form data name; the value will be transmitted
    as content. If the value is a file, the contents of the file will be sent
    as an application/octet-stream; otherwise, str(value) will be sent.
    """
    lines = []

    for (key, value) in data.items():
        lines.extend([
            '--' + boundary,
            'Content-Disposition: form-data; name="%s"' % str(key),
            '',
            str(value)
        ])

    lines.extend([
        '--' + boundary + '--',
        '',
    ])
    return '\r\n'.join(lines)


class Harness(object):
    """
    The Aspen testing harness.

    Used in tests to emulate ``GET`` and ``POST`` requests by sending them
    into a ``Website`` instance's ``respond`` method.

    Aspen does not define any User data structures or modules. If you want to
    do anything with users/sessions etc in your tests it is expected that you
    will subclass this class and add a ``add_cookie_info`` method.

    For example, in gittip a suitable subclass might be::

        class GittipTestClient(TestClient):

            def add_cookie_info(self, request, cookie_info):
                if cookie_info:
                    user = cookie_info.get('user')
                    if user is not None:
                        user = User.from_id(user)
                        # Note that Cookie needs a bytestring.
                        request.headers.cookie['session'] = user.session_token

    Example usage in a test::

        def test_api_handles_posts():
            client = TestClient(website)

            # We need to get ourselves a token!
            response = client.get('/')
            csrf_token = response.request.context['csrf_token']

            # Then, add a $1.50 and $3.00 tip
            response = client.post("/test_tippee1/tip.json",
                                {'amount': "1.00", 'csrf_token': csrf_token},
                                cookie_info={'user': 'test_tipper'})

            # Confirm we get back the right amounts in the JSON body.
            first_data = json.loads(response.body)
            assert_equal(first_data['amount'], "1.00")
    """

    def __init__(self, www, project):
        self.website = None
        self.fs = namedtuple('fs', 'www project')
        self.fs.www = www
        self.fs.project = project
        self.cookies = SimpleCookie()


    # HTTP Methods
    # ============

    def __getattr__(self, name):
        things = { 'get': self._get
                 , 'post': self._post
                 , 'website': self.website
                  }
        if name in things:
            self.website = Website([ '--www_root', self.fs.www.root
                                   , '--project_root', self.fs.project.root
                                    ])
            return things[name]


    def _get(self, path, cookie_info=None, run_through=None, **extra):
        environ = self._build_wsgi_environ(path, "GET", **extra)
        return self._perform_request(environ, cookie_info, run_through)


    def _post(self, path, data, content_type=MULTIPART_CONTENT, cookie_info=None, run_through=None,
            **extra):
        """Perform a dummy POST request against the test website.

        :param path:
            The url to perform the virutal-POST to.

        :param data:
            A dictionary or list of tuples to be encoded before being POSTed.

        Any additional parameters will be sent as headers. NOTE that in Aspen
        (request.py make_franken_headers) only headers beginning with ``HTTP``
        are included in the request - and those are changed to no longer
        include ``HTTP``. There are currently 2 exceptions to this:
        ``'CONTENT_TYPE'``, ``'CONTENT_LENGTH'`` which are explicitly checked
        for.
        """
        post_data = data

        if content_type is MULTIPART_CONTENT:
            post_data = encode_multipart(BOUNDARY, data)

        environ = self._build_wsgi_environ( path
                                         , "POST"
                                         , post_data
                                         , CONTENT_TYPE=str(content_type)
                                         , **extra
                                          )
        return self._perform_request(environ, cookie_info, run_through)


    # Hook
    # ====

    def add_cookie_info(self, request, **cookie_info):
        """Place holder function that can be replaced in a subclass.

        For example in gittip.com, it might be of interest to load session
        information into the cookie like this::

            if cookie_info:
                user = cookie_info.get('user')
                if user is not None:
                    user = User.from_id(user)
                    # Note that Cookie needs a bytestring.
                    request.headers.cookie['session'] = user.session_token
        """
        pass


    # Helpers
    # =======

    def _build_wsgi_environ(self, path, method="GET", body=None, **extra):
        environ = {}
        environ['PATH_INFO'] = path
        environ['REMOTE_ADDR'] = b'0.0.0.0'
        environ['REQUEST_METHOD'] = b'GET'
        environ['SERVER_PROTOCOL'] = b'HTTP/1.1'
        environ['HTTP_HOST'] = b'localhost'
        environ['REQUEST_METHOD'] = method
        environ['wsgi.input'] = StringIO(body)
        environ['HTTP_COOKIE'] = self.cookies.output(header='', sep='; ')
        environ.update(extra)
        return environ


    def _perform_request(self, environ, cookie_info, run_through):
        self.add_cookie_info(environ, **(cookie_info or {}))
        out = self.website.respond(environ, _run_through=run_through)
        if run_through is None:
            response = out
        else:
            response = out['response']
        if response is not None:
            if response.headers.cookie:
                self.cookies.update(response.headers.cookie)
        return out

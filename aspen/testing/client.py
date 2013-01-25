from Cookie import SimpleCookie
from StringIO import StringIO

from aspen.http.request import Request
from aspen.testing import StubWSGIRequest

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


class TestClient(object):

    def __init__(self, website):
        self.cookies = SimpleCookie()
        self.test_website = website

    def get_request(self, path, method="GET", body=None,
                    **extra):
        env = StubWSGIRequest(path)
        env['REQUEST_METHOD'] = method
        env['wsgi.input'] = StringIO(body)
        env['HTTP_COOKIE'] = self.cookies.output(header='', sep='; ')
        env.update(extra)
        return Request.from_wsgi(env)

    def perform_request(self, request, cookie_info):
        request.website = self.test_website
        self.add_cookie_info(request, cookie_info)
        response = self.test_website.handle_safely(request)
        if response.headers.cookie:
            self.cookies.update(response.headers.cookie)
        return response

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

    def post(self, path, data, content_type=MULTIPART_CONTENT,
             cookie_info=None, **extra):
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

        request = self.get_request(path, "POST", post_data,
                                   CONTENT_TYPE=str(content_type),
                                   **extra)
        return self.perform_request(request, cookie_info)

    def get(self, path, cookie_info=None, **extra):
        request = self.get_request(path, "GET")
        return self.perform_request(request, cookie_info)

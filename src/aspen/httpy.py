#!/usr/bin/env python
"""WSGI middleware to allow returning a string or Response object.

The request side of WSGI--the "commons" of the environ mapping--is quite
nice. It honors the tradition of CGI, and it's just a mapping. Simple.

The response-side API is a little stiffer, because WSGI has to support edge
cases like serving large files, complex exception handling, and HTTP/1.1
features. This results in warts like start_response, and the requirement
that apps return an iterable. The intention is that these warts be smoothed
over at other layers, and that's what we're doing here.

Apps below this shim may speak plain WSGI, but they may also return a
string, which will be sent back as text/html. They may also return or raise
a Response object.

Changes:

    - added __eq__ (to ease testing)


"""
import BaseHTTPServer
from email.Message import Message


__author__ = "Chad Whitacre <chad@zetaweb.com>"
__version__ = "1.0a1+"
__all__ = ('Responder', 'Response')


_responses = BaseHTTPServer.BaseHTTPRequestHandler.responses


class Response(StandardError):
    """Represent an HTTP Response message.
    """

    def __init__(self, code=200, body='', headers=None):
        """Takes an int, a string, and a dict.

            - code        an HTTP response code, e.g., 404
            - body        the message body as a string
            - headers     a dictionary of HTTP headers (or list of tuples)

        Body is second because one more often wants to specify a body without
        headers, than a header without a body.

        """
        if not isinstance(code, int):
            raise TypeError("'code' must be an integer")
        elif not isinstance(body, basestring):
            raise TypeError("'body' must be a string")
        elif headers is not None and not isinstance(headers, (dict, list)):
            raise TypeError("'headers' must be a dictionary or a list of " +
                            "2-tuples")

        StandardError.__init__(self)
        self.code = code
        self.body = body
        self.headers = Message()
        if headers:
            if isinstance(headers, dict):
                headers = headers.items()
            for k, v in headers:
                self.headers[k] = v


    def __repr__(self):
        return "<Response: %s>" % str(self)

    def __str__(self):
        return "%d %s" % (self.code, self._status()[0])

    def __eq__(self, other):
        try:
            assert self.code == other.code
            assert self.body == other.body
            for k in self.headers.keys():
                assert k in other.headers
                assert self.headers[k] == other.headers[k]
            return True
        except AssertionError:
            return False

    def _status(self):
        return _responses.get(self.code, ('???','Unknown HTTP status'))


    def __call__(self, environ, start_response):
        """We ourselves are a WSGI app.

        XXX: WSGI exception handling?

        """
        _status = self._status()

        status = "%d %s" % (self.code, _status[0])
        headers = [(str(k), str(v)) for k,v in self.headers.items()]
        body = [self.body and self.body or _status[1]]

        start_response(status, headers)
        return body


class Responder(object):
    """WSGI middleware to also allow returning a string or Response object.
    """

    def __init__(self, app):
        self.wrapped_app = app

    def __call__(self, environ, start_response):
        try:
            response = self.wrapped_app(environ, start_response)
        except Response, response:
            pass
        except:
            raise

        if isinstance(response, Response):
            response = response(environ, start_response)
        elif isinstance(response, basestring):
            response = Response(200, response)
            response.headers['Content-Type'] = 'text/html'
            response = response(environ, start_response)

        return response


if __name__ == '__main__':
    """Simple smoke test.

    Hit http://localhost:8080/ in a web browser after running this script. Only
    one of the calls to Server can be uncommented or you'll get:

      socket.error: (48, 'Address already in use')

    """
    from wsgiref.simple_server import make_server # included w/ Python 2.5

    Server = lambda app: make_server('', 8080, app)
    app = lambda e, s: "Greetings, program!"

    def app2(environ, start_response):
        return Response( 200, "Greetings, program!"
                       , {'Content-Type':'text/plain'}
                        )

    server = Server(Responder(app)) # tests returning a string
    #server = Server(Responder(app2)) # tests returning a Response
    #server = Server(app) # unwrapped; raises AssertionError when hit

    server.serve_forever()


""" <http://opensource.org/licenses/bsd-license.php>
Copyright (c) 2006, Chad Whitacre <chad@zetaweb.com>
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

  * Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

  * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

  * Neither the name of Chad Whitacre nor the names of any other contributors
    or copyright holders may be used to endorse or promote products derived
    from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

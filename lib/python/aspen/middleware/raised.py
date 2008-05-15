"""WSGI middleware to catch a raised Response object, also defined here.
"""
__all__ = ('Response', 'middleware')


import BaseHTTPServer
from email.Message import Message


_responses = BaseHTTPServer.BaseHTTPRequestHandler.responses


class Response(StandardError):
    """Represent an HTTP Response message.
    """

    def __init__(self, code=200, headers=None, body=None):
        """Takes an int, a string or iterable, and a dict.

            - code        an HTTP response code, e.g., 404
            - headers     a dictionary of HTTP headers (or list of tuples)
            - body        the message body as a string or iterable

        """
        if not isinstance(code, int):
            raise TypeError("'code' must be an integer")
        elif headers is not None and not isinstance(headers, (dict, list)):
            raise TypeError("'headers' must be a dictionary or a list of " +
                            "2-tuples")

        StandardError.__init__(self)
        self.code = code
        self.headers = Message()
        if headers is not None:
            if isinstance(headers, dict):
                headers = headers.items()
            for k, v in headers:
                self.headers[k] = v
        self.body = body


    def __repr__(self):
        return "<Response: %s>" % str(self)

    def __str__(self):
        return "%d %s" % (self.code, self._status()[0])

    def _status(self):
        return _responses.get(self.code, ('???','Unknown HTTP status'))


    def __call__(self, environ, start_response):
        """We ourselves are a WSGI app.

        XXX: WSGI exception handling?

        """
        _status = self._status()

        status = "%d %s" % (self.code, _status[0])
        headers = [(str(k), str(v)) for k,v in self.headers.items()]
        body = self.body 
        if body is None:
            body = [_status[1]] # standard HTTP status message, e.g., 'OK' 
        elif isinstance(body, basestring):
            body = [body]
        
        start_response(status, headers)
        return body


def middleware(next):
    """WSGI middleware to catch raised Response objects.

    For the record, wsgiserver.py enforces the only-call-start_response-once
    requirement (unless exc_info is not None). 

    """
    def wsgi(environ, start_response):
        try:
            response = next(environ, start_response)
        except Response, response:
            response = response(environ, start_response) # it's a WSGI callable
        return response
    return wsgi


if __name__ == '__main__':
    """Simple smoke test.

    Hit http://localhost:8080/ in a web browser after running this script. Only
    one of the calls to Server can be uncommented or you'll get:

      socket.error: (48, 'Address already in use')

    """
    from wsgiref.simple_server import make_server # included w/ Python 2.5
    Server = lambda app: make_server('', 8080, app)
    def app(e,s): raise Response(200, "Greetings, program!")
    server = Server(middleware(app)) # tests returning a string
    #server = Server(app) # unwrapped; Response exception logged as a 500
    server.serve_forever()


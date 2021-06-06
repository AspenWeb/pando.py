"""
:mod:`httpbasic`
----------------

HTTP Basic Auth module for Pando.

To use::

    # import it
    from pando.auth import httpbasic

    # configure it - see the docs on the BasicAuth object for args to inbound_responder()
    auth = httpbasic.inbound_responder(my_password_verifier)

    # install it
    website.state_chain.insert_after('parse_environ_into_request', auth)

"""

import base64
import binascii

from .. import Response


def inbound_responder(*args, **kwargs):
    """ see BasicAuth object for args; they're passed through """
    auth = BasicAuth(*args, **kwargs)
    def httpbasic_inbound_responder(request):
        """generated request-handling method"""
        request.auth = BAWrapper(auth, request)
        authed, response = auth.authorized(request)
        if not authed:
            raise response
    return httpbasic_inbound_responder


class BAWrapper:
    """A convenience wrapper for BasicAuth handler to put on the request
    object so the user can do 'request.auth.username()'
    instead of 'request.auth.username(request)'
    """

    def __init__(self, basicauth, request):
        self.auth = basicauth
        self.request = request

    def authorized(self):
        return self.auth.authorized(self.request)

    def username(self):
        return self.auth.username(self.request)

    def logout(self):
        return self.auth.logout(self.request)


class BasicAuth:
    """An HTTP Basic Auth handler for Pando."""

    def __init__(self, verify_password, html=None, realm=b'protected'):
        """Constructor for an HTTP Basic Auth handler.

        :param verify_password: a function that, when passed the args
            (user, password), will return True iff the password is
            correct for the specified user
        :param html: The HTML page to return along with a 401 'Not
            Authorized' response. Has a reasonable default
        :param realm: the name of the auth realm

        """
        failhtml = html or b'''Not Authorized. <a href="#">Try again.</a>'''
        self.verify_password = verify_password
        fail_header = {b'WWW-Authenticate': b'Basic realm="' + realm + b'"'}
        self.fail_401 = Response(401, failhtml, fail_header)
        self.fail_400 = Response(400, failhtml, fail_header)
        self.logging_out = set([])

    def authorized(self, request):
        """Returns whether this request passes Basic auth or not, and
           the Response to raise if not
        """
        header = request.headers.get(b'Authorization', b'')
        if not header:
            #print("no auth header.")
            # no auth header at all
            return False, self.fail_401
        if not header.startswith(b'Basic'):
            #print("not a Basic auth header.")
            # not a basic auth header at all
            return False, self.fail_400
        try:
            userpass = base64.b64decode(header[len(b'Basic '):])
        except (binascii.Error, TypeError):
            # malformed user:pass
            return False, self.fail_400
        if not b':' in userpass:
            # malformed user:pass
            return False, self.fail_400
        user, passwd = userpass.split(b':', 1)
        if user in self.logging_out:
            #print("logging out, so failing once.")
            self.logging_out.discard(user)
            return False, self.fail_401
        if not self.verify_password(user, passwd):
            #print("wrong password.")
            # wrong password
            # TODO: add a max attempts per timespan to slow down bot attacks
            return False, self.fail_401
        return True, None

    def username(self, request):
        """Returns the username in the current Auth header"""
        header = request.headers.get(b'Authorization', b'')
        if not header.startswith(b'Basic'):
            return None
        userpass = base64.b64decode(header[len(b'Basic '):])
        if not b':' in userpass:
            return None
        user, _ = userpass.split(b':', 1)
        return user

    def logout(self, request):
        """Will force the next auth request (ie. HTTP request) to fail,
            thereby prompting the user for their username/password again
        """
        self.logging_out.add(self.username(request))
        return request


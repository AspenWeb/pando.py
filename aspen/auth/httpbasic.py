
import base64

from aspen import Response


def inbound_responder(*args, **kwargs):
    """ see BasicAuth object for args; they're passed through """
    auth = BasicAuth(*args, **kwargs)
    def _(request):
        request.auth = BAWrapper(auth, request)
        authed, response = auth.authorized(request)
        if not authed:
            raise response
        return request
    return _


class BAWrapper(object):
    """A wrapper for BasicAuth handler that is a nice object to put on the request object
       so the user can do 'request.auth.userName()' instead of 'request.auth.userName(request)'
       """
    def __init__(self, basicauth, request):
        self.auth = basicauth
        self.request = request

    def authorized(self):
        return self.auth.authorized(self.request)

    def userName(self):
        return self.auth.userName(self.request)

    def logout(self):
        return self.auth.logout(self.request)


class BasicAuth(object):
    """An HTTP BASIC AUTH handler for Aspen."""

    def __init__(self, verify_password, html=None, realm='protected'):
        """Constructor for an HTTP BASIC AUTH handler.

        :verify_password - a function that, when passed the args (user, password), will return True iff the password is correct for the specified user
        :html - The HTML page to reutrn along with a 401 'Not Authorized' response. Has a reasonable default
        :realm - the name of the auth realm 
        """
        failhtml =  html or '''Not Authorized. <a href="#">Try again.</a>'''
        self.verify_password = verify_password
        self.fail_response = Response(401, failhtml, { 'WWW-Authenticate': 'Basic realm="%s"' % realm })
        self.logging_out = set([])

    def authorized(self, request):
        """Returns whether this request passes BASIC auth or not, and the Response to raise if not"""
        header = request.headers.get('Authorization', '')
        if not header.startswith('Basic'):
            print("no auth header.")
            # no auth header at all
            return False, self.fail_response
        userpass = base64.b64decode(header[len('Basic '):])
        if not ':' in userpass:
            # malformed user:pass
            return False, self.fail_response
        user, passwd = userpass.split(':',1)
        if user in self.logging_out:
            print("logging out, so failing once.")
            self.logging_out.discard(user)
            return False, self.fail_response
        if not self.verify_password(user, passwd):
            print("wrong password.")
            # wrong password
            # TODO: add a max attempts per timespan to slow down bot attacks
            return False, self.fail_response
        return True, None

    def userName(self, request):
        """Returns the username in the current Auth header"""
        header = request.headers.get('Authorization', '')
        if not header.startswith('Basic'):
            return None
        userpass = base64.b64decode(header[len('Basic '):])
        if not ':' in userpass:
            return None
        user, passwd = userpass.split(':',1)
        return user        

    def logout(self, request):
        """Will force the next auth request (ie. HTTP request) to fail, thereby prompting the user for their username/password again"""
        self.logging_out.add(self.userName(request))
        return request


"""
aspen.auth.httpdigest
~~~~~~~~~~~~~~~~~~~~~
"""
# Originally by Josh Goldoot
# version 0.01
#  Public domain.
# from http://www.autopond.com/digestauth.py
# modified by Paul Jimenez

import random, time, re

from aspen.backcompat import md5

class MalformedAuthenticationHeader(Exception): pass

## wrapper bits

class AspenHTTPProvider:
    """An abstraction layer between the Auth object and
    http-framework specific code."""

    def __init__(self, request):
        self.request = request

    def _response(self, *args):
        from aspen import Response
        r = Response(*args)
        r.request = self.request
        return r

    def set_request(self, request):
        self.request = request

    def auth_header(self, default):
        return self.request.headers.get('Authorization', default)

    def user_agent(self):
        return self.request.headers.get('User-Agent') or b''

    def request_method(self):
        return self.request.line.method

    def path_and_query(self):
        return self.request.line.uri.raw

    def send_400(self, html, extraheaders):
        return self._response(400, html, extraheaders)

    def send_401(self, html, extraheaders):
        return self._response(401, html, extraheaders)

    def send_403(self, html, extraheaders):
        return self._response(403, html, extraheaders)


## make a generator of containers that aspen will like

def inbound_responder(*args, **kw):
    """ This should be used in your configure-aspen.py like so:

    import aspen.auth.httpdigest as digestauth

    def get_digest(username, realm):
        users = { 'guest':'guest',
                }
        password = users[username]
        return digestauth.digest(':'.join([username, realm, password]))

    auth = digestauth.inbound_responder(get_digest)
    website.algorithm.insert_after('parse_environ_into_request', auth)
    """
    kwargs = kw.copy()
    kwargs['http_provider'] = AspenHTTPProvider
    auth = Auth(*args, **kwargs)
    def httpdigest_inbound_responder(request):
        """generated hook function"""
        request.auth = AspenAuthWrapper(auth, request)
        authed, response = auth.authorized(request)
        if not authed:
            #print "Response: %s" % repr(response.headers)
            raise response
        return request
    return httpdigest_inbound_responder


class AspenAuthWrapper(object):
    """Convenience class to put on a request that
       has a reference to the request its on so accessing
       auth methods doesn't require repeating the request arg.
    """

    def __init__(self, auth, request):
        self.auth = auth
        self.request = request

    def authorized(self):
        """delegates to self.auth object"""
        return self.auth.authorized(self.request)[0]

    def username(self):
        """delegates to self.auth object"""
        return self.auth.username(self.request)

    def logout(self):
        """delegates to self.auth object"""
        return self.auth.logout(self.request)


## Fundamental utilities

class Storage(dict):
    """
    (from web.py)
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.

        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'

    """
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k

    def __repr__(self):
        return '<Storage ' + dict.__repr__(self) + '>'


## Actual authentication obj

class Auth(object):
    """A decorator class implementing digest authentication (RFC 2617)"""
    def __init__(self,  get_digest,  realm="Protected",  tolerate_ie = True, redirect_url = '/newuser',  unauth_html = None,  nonce_skip = 0,  lockout_time = 20,  nonce_life = 180,  tries=3,  domain=[], http_provider=None):
        """Creates a decorator specific to a particular web application.
            get_digest: a function taking the arguments (username, realm), and returning digestauth.digest(username:realm:password), or
                            throwing KeyError if no such user
            realm: the authentication "realm"
            tolerate_ie: don't deny requests from Internet Explorer, even though it is standards uncompliant and kind of insecure
            redirect_url:  when user hits "cancel," they are redirected here
            unauth_html:  the HTML that is sent to the user and displayed if they hit cancel (default is a redirect page to redirect_url)
            nonce_skip: tolerate skips in the nonce count, only up to this amount (useful if CSS or JavaScript is being loaded unbeknownst to your code)
            lockout_time: number of seconds a user is locked out if they send a wrong password (tries) times
            nonce_life: number of seconds a nonce remains valid
            tries: number of tries a user gets to enter a correct password before the account is locked for lockout_time seconds
            http_provider: interface to HTTP protocol workings (see above code)
        """
        self.http_provider = http_provider
        if self.http_provider is None:
            raise Exception("no http_provider provided")
        self.get_digest,  self.realm,  self.tolerate_ie  = (get_digest,  realm,  tolerate_ie)
        self.lockout_time,  self.tries,  self.nonce_life,  self.domain = (lockout_time,  tries - 1,  nonce_life,  domain)
        self.unauth_html = unauth_html or self._default_401_html.replace("$redirecturl",  redirect_url)
        self.outstanding_nonces = NonceMemory()
        self.outstanding_nonces.set_nonce_skip(nonce_skip)
        self.user_status = {}
        self.opaque = "%032x" % random.getrandbits(128)

    _default_401_html = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="REFRESH" content="1; URL=$redirecturl" />
  <title></title>
</head>
<body>
</body>
</html>
"""

    def authorized(self, request):
        """ is this request authorized?
            returns a tuple where the first value is true if so and false if not, and the second value is the response to return
        """
        http = self.http_provider(request)
        request_header = http.auth_header(None)
        if not request_header:
            # client has failed to include an authentication header; send a 401 response
            return False, self._send_401_unauth_response(http, "No auth header")
        if request_header[0:7] != "Digest ":
            # client has attempted to use something other than Digest authenication; deny
            return False, self._deny_bad_request(http)
        req_header_dict = parse_auth_header(request_header)
        if not self._directive_proper(http.user_agent(), req_header_dict, http.path_and_query()):
            # Something is wrong with the authentication header
            if req_header_dict.get('opaque', self.opaque) != self.opaque:
                # Didn't send back the correct "opaque;" probably, our server restarted.  Just send
                # them another authentication header with the correct opaque field.
                return False, self._send_401_unauth_response(http, "Incorrect opaque field.")
            else:
                # Their header had a more fundamental problem.  Something is fishy.  Deny access.
                return False, self._deny_bad_request(http, "Authorization Request Header does not conform to RFC 2617 section 3.2.2")
        # if user sent a "logout" nonce, make them type in the password again
        if len(req_header_dict['nonce']) != 34:
            return False, self._send_401_unauth_response(http, "Logged out.")
        nonce_response = self.outstanding_nonces.nonce_state(req_header_dict)
        if nonce_response == NonceMemory.NONCE_INVALID:
            # Client sent a nonce we've never heard of before
            return False, self._deny_bad_request(http)
        if nonce_response == NonceMemory.NONCE_OLD:
            # Client sent an old nonce.  Give the client a new one, and ask to authenticate again before continuing.
            return False, self._send_401_unauth_response(http, "Stale nonce. Try again.", stale=True)
        username = req_header_dict['username']
        status = self.user_status.get(username, (self.tries, 0))
        if status[0] < 1 and time.time() < status[1]:
            # User got the password wrong within the last (self.lockout_time) seconds
            return False, self._deny_forbidden(http)
        if status[0] < 1:
            # User sent the wrong password, but more than (self.lockout_time) seconds have passed, so give
            # them another try.  However, send a 401 header so user's browser prompts for a password
            # again.
            self.user_status[username] = (1, 0)
            return False, self._send_401_unauth_response(http, "Wrong password, try again.")
        if self._request_digest_valid(req_header_dict, http.request_method()):
            # User authenticated; forgive any past incorrect passwords and run the function we're decorating
            self.user_status[username] = (self.tries, 0)
            return True, None
        else:
            # User entered the wrong password.  Deduct one try, and lock account if necessary
            self.user_status[username] = (status[0] - 1, time.time() + self.lockout_time)
            self._log_incorrect_password(username,  req_header_dict)
            return False, self._send_401_unauth_response(http, "Wrong password. One try burned.")

    def _log_incorrect_password(self,  username,  req_header_dict):
        """Hook to log incorrrect password attempts"""
        pass  # Do your own logging here

    def _directive_proper(self,  user_agent, req_header_dict, req_path):
        """Verifies that the client's authentication header contained the required fields"""
        for variable in ['username', 'realm', 'nonce', 'uri', 'response', 'cnonce', 'nc']:
            if variable not in req_header_dict:
                return False
        # IE doesn't send "opaque" and does not include GET parameters in the Digest field
        standards_uncompliant = self.tolerate_ie and ("MSIE" in user_agent)
        return req_header_dict['realm'] == self.realm \
            and (standards_uncompliant or req_header_dict.get('opaque','') == self.opaque) \
            and len(req_header_dict['nc']) == 8 \
            and (req_header_dict['uri'] == req_path or (standards_uncompliant and "?" in req_path and req_path.startswith(req_header_dict['uri'])))

    def _request_digest_valid(self, req_header_dict, req_method):
        """Checks to see if the client's request properly authenticates"""
        # Ask the application for the hash of A1 corresponding to this username and realm
        try:
            HA1 = self.get_digest(req_header_dict['username'], req_header_dict['realm'])
        except KeyError:
            # No such user
            return False
        qop = req_header_dict.get('qop','auth')
        A2 = req_method + ':' + req_header_dict['uri']
        # auth-int stuff would go here, but few browsers support it
        nonce = req_header_dict['nonce']
        # Calculate the response we should have received from the client
        correct_answer = digest(":".join([HA1, nonce, req_header_dict['nc'], req_header_dict['cnonce'], qop, digest(A2) ]))
        # Compare the correct response to what the client sent
        return req_header_dict['response'] == correct_answer

    def _send_401_unauth_response(self, http, why_msg, stale=False):
        """send a 401, optionally with a stale flag"""
        nonce = self.outstanding_nonces.get_new_nonce(self.nonce_life)
        challenge_list = [ "realm=" + quote_it(self.realm),
                           'qop="auth"',
                           'nonce=' + quote_it(nonce),
                           'opaque=' + quote_it(self.opaque)
                         ]
        if self.domain: challenge_list.append( 'domain=' + quote_it(" ".join(self.domain)) )
        if stale: challenge_list.append( 'stale="true"')
        extraheaders = [("WWW-Authenticate", "Digest " + ",".join(challenge_list)),
                        ("Content-Type","text/html"),
                        ("X-Why-Auth-Failed", why_msg)]
        return http.send_401(self.unauth_html, extraheaders)

    def _deny_bad_request(self, http, info=""):
        return http.send_400(info, [('Content-Type', 'text/html')])

    def _deny_forbidden(self, http):
        """Sent when user has entered an incorrect password too many times"""
        return http.send_403(self.unauth_html, [('Content-Type', 'text/html')])

    def _get_valid_auth_header(self, http):
        """returns valid dictionary of authorization header, or None"""
        request_header = http.auth_header(None)
        if not request_header:
            raise MalformedAuthenticationHeader()
        if request_header[0:7] != "Digest ":
            raise MalformedAuthenticationHeader()
        req_header_dict = parse_auth_header(request_header)
        if not self._directive_proper(http.user_agent(), req_header_dict, http.path_and_query()):
            raise MalformedAuthenticationHeader()
        return req_header_dict

    def logout(self, request):
        """Cause user's browser to stop sending correct authentication requests until user re-enters password"""
        http = self.http_provider(request)
        try:
            req_header_dict = self._get_valid_auth_header(http)
        except MalformedAuthenticationHeader:
            return
        if len(req_header_dict['nonce']) == 34:
            # First time: send a 401 giving the user the fake "logout" nonce
            nonce = "%032x" % random.getrandbits(136)
            challenge_list = [ "realm=" + quote_it(self.realm),
                               'qop="auth"',
                               'nonce=' + quote_it(nonce),
                               'opaque=' + quote_it(self.opaque),
                               'stale="true"']
            extraheaders = [("WWW-Authenticate", "Digest " + ",".join(challenge_list))]
            return http.send_401(None, extraheaders)

    def username(self, request):
        """Returns the HTTP username, or None if not logged in."""
        http = self.http_provider(request)
        try:
            req_header_dict = self._get_valid_auth_header(http)
        except MalformedAuthenticationHeader:
            return None
        if len(req_header_dict['nonce']) != 34:
            return None
        nonce_response = self.outstanding_nonces.nonce_state(req_header_dict)
        if nonce_response != NonceMemory.NONCE_VALID:
            # Client sent a nonce we've never heard of before
            # Client sent an old nonce.  Give the client a new one, and ask to authenticate again before continuing.
            return None
        return req_header_dict.username



def digest(data):
    """Return a hex digest MD5 hash of the argument"""
    return md5(data).hexdigest()

def quote_it(s):
    """Return the argument quoted, suitable for a quoted-string"""
    return '"%s"' % (s.replace("\\","\\\\").replace('"','\\"'))

## Code to parse the authentication header
parse_auth_header_re = re.compile(r"""
    (   (?P<varq>[a-z]+)="(?P<valueq>.+?)"(,|$)    )   # match variable="value", (terminated by a comma or end of line)
    |
    (   (?P<var>[a-z]+)=(?P<value>.+?)(,|$)    )          # match variable=value,  (same as above, but no quotes)
    """,  re.VERBOSE | re.IGNORECASE )
def parse_auth_header(header):
    """parse an authentication header into a dict"""
    result = Storage()
    for m in parse_auth_header_re.finditer(header):
        g = m.groupdict()
        if g['varq'] and g['valueq']:
            result[g['varq']] = g['valueq'].replace(r'\"',  '"')
        elif g['var'] and g['value']:
            result[g['var']] = g['value']
    return result

class NonceMemory(dict):
    """
    A dict of in-use nonces, with a couple methods to create new nonces and get the state of a nonce
    """

    NONCE_VALID = 1
    NONCE_INVALID = 2
    NONCE_OLD = 3

    def set_nonce_skip(self, nonce_skip):
        self.nonce_skip = nonce_skip

    def get_new_nonce(self,  lifespan = 180):
        """Generate a new, unused nonce, with a nonce-count set to 1.
            :lifespan - how long (in seconds) the nonce is good for before it's considered 'old'
        """
        is_new = False
        while not is_new:
            nonce = "%034x" % random.getrandbits(136)  # a random 136-bit zero-padded lowercase hex string
            is_new = not nonce in self
        self[nonce] = (time.time() + lifespan, 1)
        return nonce

    def nonce_state(self, req_header_dict):
        """ 1 = nonce valid, proceed; 2 = nonce totally invalid;  3 = nonce requires refreshing """
        nonce = req_header_dict.get('nonce', None)
        exp_time, nCount = self.get(nonce, (0, 0) )
        if exp_time == 0:
            # Client sent some totally unknown nonce -- reject
            return self.NONCE_INVALID
        try:
            incoming_nc = int((req_header_dict['nc']), 16)
        except ValueError:
            return self.NONCE_INVALID # the "nc" field was deformed (not hexadecimal); reject
        # default nonce_skip value
        nonce_skip = getattr(self, 'nonce_skip', 1)
        if exp_time == 1 or nCount > 1000 or exp_time < time.time() or incoming_nc - nCount > nonce_skip:
            # Client sent good nonce, but it is too old, or the count has gotten screwed up; give them a new one
            del self[nonce]
            return self.NONCE_OLD
        self[nonce] = (exp_time, incoming_nc + 1)
        return self.NONCE_VALID


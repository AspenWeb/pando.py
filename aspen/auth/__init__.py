"""
aspen.auth
++++++++++

Aspen's Auth modules.

Currently:

    * cookie - Cookie Auth
    * httpbasic - HTTP BASIC Auth
    * httpdigest - HTTP DIGEST Auth

"""
from aspen import Response
from aspen.utils import typecheck


class BaseUser(object):

    def __init__(self, token):
        typecheck(token, (unicode, None))
        self.token = token

    @property
    def ANON(self):
        return self.token is None

User = BaseUser


def require_authentication(request):
    """Given a request object, return None or raise Response(401).

    Place this after hooks that will set request.context['user']. Use hook
    filters to apply this to less than all requests. Use a 401.html file to
    influence what happens when 401 is raised here.

    """
    if request.context['user'].ANON:
        raise Response(401)

"""
Aspen's Auth modules.

Currently:

    * cookie - Cookie Auth
	* httpbasic - HTTP BASIC Auth
	* httpdigest - HTTP DIGEST Auth

"""
from aspen.utils import typecheck


class BaseUser(object):

    def __init__(self, token):
        typecheck(token, (unicode, None))
        self.token = token

    @property
    def ANON(self):
        return self.token is None

User = BaseUser

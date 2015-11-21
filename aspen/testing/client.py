"""
aspen.testing.client
~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ..website import Website


class Client(object):
    """This is the Aspen test client. It is probably useful to you.
    """

    def __init__(self, www_root=None, project_root=None):
        self.www_root = www_root
        self.project_root = project_root
        self._website = None


    def hydrate_website(self, **kwargs):
        if (self._website is None) or kwargs:
            _kwargs = { 'www_root': self.www_root
                      , 'project_root': self.project_root
                       }
            _kwargs.update(kwargs)
            self._website = Website(**_kwargs)
        return self._website

    website = property(hydrate_website)


    # HTTP Methods
    # ============

    def _hit(self, method, path='/', querystring='', raise_immediately=True, return_after=None,
            want='response', **headers):

        state = self.website.respond( path
                                    , querystring
                                    , accept_header=None
                                    , raise_immediately=raise_immediately
                                    , return_after=return_after
                                     )

        response = state.get('response')
        if response is not None:
            if response.headers.cookie:
                self.cookie.update(response.headers.cookie)

        attr_path = want.split('.')
        base = attr_path[0]
        attr_path = attr_path[1:]

        out = state[base]
        for name in attr_path:
            out = getattr(out, name)

        return out

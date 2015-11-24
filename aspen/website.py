"""
aspen.website
+++++++++++++
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from algorithm import Algorithm
from .configuration import Configurable


class Website(Configurable):
    """Represent a website.

    This object holds configuration information, and how to handle HTTP
    requests (per WSGI). It is available to user-developers inside of their
    simplates and algorithm functions.

    """

    def __init__(self, **kwargs):
        """Takes configuration in kwargs.
        """
        self.algorithm = Algorithm.from_dotted_name('aspen.algorithm')
        self.configure(**kwargs)


    def respond(self, path, querystring, accept_header, raise_immediately=None, return_after=None):
        """Given a WSGI environ, return a state dict.
        """
        return self.algorithm.run( website=self
                                 , path=path
                                 , querystring=querystring
                                 , accept_header=accept_header
                                 , _raise_immediately=raise_immediately
                                 , _return_after=return_after
                                  )

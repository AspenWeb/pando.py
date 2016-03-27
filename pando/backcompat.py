"""
pando.backcompat
++++++++++++++++
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

try:                # 2
    from Cookie import CookieError, SimpleCookie
except ImportError: # 3
    from http.cookies import CookieError, SimpleCookie

try:                # 3
    from html import escape as html_escape
except ImportError: # 2
    from cgi import escape as cgi_escape
    def html_escape(*args,**kwargs):
        # make the defaults match the py3 defaults
        kwargs['quote'] = kwargs.get('quote', True)
        return cgi_escape(*args,**kwargs)

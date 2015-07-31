"""
aspen.resource.static_resource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from .. import Response

class StaticResource():

    def __init__(self, website, fs, raw, media_type):
        self.website = website
        self.fs = fs
        self.raw = raw
        self.media_type = media_type
        if media_type == 'application/json':
            self.media_type = self.website.media_type_json

    def respond(self, context):
        response = context.get('response', Response())
        # XXX Perform HTTP caching here.
        assert type(self.raw) is str # sanity check
        response.body = self.raw
        response.headers['Content-Type'] = self.media_type
        if self.media_type.startswith('text/'):
            charset = self.website.charset_static
            if charset is None:
                pass # Let the browser guess.
            else:
                response.charset = charset
                response.headers['Content-Type'] += '; charset=' + charset
        return response

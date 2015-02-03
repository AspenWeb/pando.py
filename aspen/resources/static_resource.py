"""
aspen.resource.static_resource
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from aspen import Response
from aspen.resources.resource import Resource


class StaticResource(Resource):

    def __init__(self, *a, **kw):
        Resource.__init__(self, *a, **kw)
        if self.media_type == 'application/json':
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

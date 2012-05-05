from aspen import Response
from aspen.resources.resource import Resource


class StaticResource(Resource):

    def __init__(self, *a, **kw):
        Resource.__init__(self, *a, **kw)
        if self.media_type == 'application/json':
            self.media_type = self.website.media_type_json

    def respond(self, request, response=None):
        """Given a Request and maybe a Response, return or raise a Response.
        """
        response = response or Response()
        # XXX Perform HTTP caching here.
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

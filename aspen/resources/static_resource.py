from aspen import Response
from aspen.resources.resource import Resource


class StaticResource(Resource):

    def __init__(self, *a, **kw):
        super(StaticResource, self).__init__(*a, **kw)
        if self.mimetype == 'application/json':
            self.mimetype = self.website.media_type_json

    def respond(self, request, response=None):
        """Given a Request and maybe a Response, return or raise a Response.
        """
        response = response or Response()
        # XXX Perform HTTP caching here.
        response.body = self.raw
        response.headers['Content-Type'] = self.mimetype
        if self.mimetype.startswith('text/'):
            charset = self.website.charset_static
            if charset is None:
                pass # Let the browser guess.
            else:
                response.headers['Content-Type'] += '; charset=' + charset
        return response

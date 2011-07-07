from aspen import Response
from aspen.resources.resource import Resource


class StaticResource(Resource):

    def __init__(self, *a, **kw):
        super(StaticResource, self).__init__(*a, **kw)
        self.nbytes = len(self.raw)
        if self.mimetype == 'application/json':
            self.mimetype = self.website.json_content_type

    def render(self, request, response=None):
        """Given a Request and maybe a Response, return or raise a Response.
        """
        response = response or Response()
        # XXX Perform HTTP caching here.
        response.body = self.raw
        response.headers.set('Content-Type', self.mimetype)
        response.headers.set('Content-Length', self.nbytes)
        return response

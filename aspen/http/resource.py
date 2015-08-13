from .response import Response
from ..simplates import Simplate, SimplateDefaults, SimplateException


class Static(object):
    """Model a static HTTP resource.
    """

    def __init__(self, website, fspath, raw, media_type):
        self.website = website
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


class Dynamic(Simplate):
    """Model a dynamic HTTP resource using simplates.

       Most defaults are in website, so make SimplateDefaults from that.

       Make .website available as it has been historically.

       Figure out which accept header to use.

       Append a charset to text Content-Types if one is known.


    """

    def __init__(self, website, fs, raw, default_media_type):
        self.website = website
        initial_context = { 'website': website }
        defaults = SimplateDefaults(website.default_renderers_by_media_type,
                                    website.renderer_factories,
                                    initial_context)
        super(Dynamic, self).__init__(defaults, fs, raw, default_media_type)

    def respond(self, state):
        accept = dispatch_accept = state['dispatch_result'].extra.get('accept')
        if accept is None:
            accept = state.get('accept_header')
        try:
            content_type, body = super(Dynamic, self).respond(accept, state)
            response = state['response']
            response.body = body
            if 'Content-Type' not in response.headers:
                if content_type.startswith('text/') and response.charset is not None:
                    content_type += '; charset=' + response.charset
                response.headers['Content-Type'] = content_type
            return response
        except SimplateException as e:
            # find an Accept header
            if dispatch_accept is not None:  # indirect negotiation
                raise Response(404)
            else:                            # direct negotiation
                msg = "The following media types are available: %s."
                msg %= ', '.join(e.available_types)
                raise Response(406, msg.encode('US-ASCII'))


"""Implements rendered resources.

Problems with tornado.template:

    - no option to fail silently
    - Loader cache doesn't account for mtime
    - Is this a bug?

        {{ foo }}
        {% for foo in [1,2,3] %}
        {% end %}

    - can't do this:

        {% if ... %}
            {% extends %}
        {% else %}
            {% extends %}
        {% end %}

"""
from aspen.resources.negotiated_resource import NegotiatedResource
from aspen.utils import typecheck


class RenderedResource(NegotiatedResource):
    """Model a limiting case of negotiated resources.

    A negotiated resource has multiple content pages, one per media type, with
    the media type of each explicitly specified in-line. A rendered resource
    has one content page, and the media type is inferred from the file
    extension. In both cases the rendering machinery is used to transform the
    bytes in each page into output for the wire.

    """

    min_pages = 2
    max_pages = 4


    def parse_into_pages(self, raw):
        """Extend to insert page one if needed.
        """
        pages = NegotiatedResource.parse_into_pages(self, raw)
        npages = len(pages)
        assert npages in (2, 3, 4), npages  # sanity check
        if npages == 2:
            pages = [''] + pages
        return pages


    def _parse_specline(self, specline):
        """Override to simplify.

        Rendered resources have a simpler specline than negotiated resources.
        They don't have a media type, and the renderer is optional.

        """
        typecheck(specline, str)

        renderer = specline
        media_type = self.media_type

        if not renderer:
            renderer = self.website.default_renderers_by_media_type[media_type]
            renderer = "#!" + renderer

        make_renderer = self._get_renderer_factory(media_type, renderer)

        return (make_renderer, media_type)

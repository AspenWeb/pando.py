from aspen import resources, Response
from aspen.resources.negotiated_resource import NegotiatedResource
from aspen.testing import assert_raises, attach_teardown, handle, mk, StubRequest
from aspen.website import Website
from aspen.renderers.tornado import Factory as TornadoFactory


def get(**_kw):
    kw = dict( website = Website([])
             , fs = ''
             , raw = '^L^L #!tornado text/plain\n'
             , media_type = ''
             , mtime = 0
              )
    kw.update(_kw)
    return NegotiatedResource(**kw)


def test_negotiated_resource_is_instantiable():
    website = Website([])
    fs = ''
    raw = '^L^L #!tornado text/plain\n'
    media_type = ''
    mtime = 0
    actual = NegotiatedResource(website, fs, raw, media_type, mtime).__class__
    assert actual is NegotiatedResource, actual


# compile_page

def test_compile_page_chokes_on_truly_empty_page():
    assert_raises(SyntaxError, get().compile_page, '\n', '')

def test_compile_page_compiles_empty_page():
    page = get().compile_page(' text/html\n', '')
    actual = page[0]({}), page[1]
    assert actual == ('', 'text/html'), actual

def test_compile_page_compiles_page():
    page = get().compile_page(' text/html\nfoo bar', '')
    actual = page[0]({}), page[1]
    assert actual == ('foo bar', 'text/html'), actual


# _parse_specline

def test_parse_specline_parses_specline():
    factory, media_type = get()._parse_specline('#!tornado media/type')
    actual = (factory.__class__, media_type)
    assert actual == (TornadoFactory, 'media/type'), actual

def test_parse_specline_doesnt_require_renderer():
    factory, media_type = get()._parse_specline('media/type')
    actual = (factory.__class__, media_type)
    assert actual == (TornadoFactory, 'media/type'), actual

def test_parse_specline_requires_media_type():
    assert_raises(SyntaxError, get()._parse_specline, '#!tornado')

def test_parse_specline_raises_SyntaxError_if_renderer_is_malformed():
    assert_raises(SyntaxError, get()._parse_specline, 'tornado media/type')

def test_parse_specline_raises_SyntaxError_if_media_type_is_malformed():
    assert_raises(SyntaxError, get()._parse_specline, '#!tornado media-type')

def test_parse_specline_cant_mistake_malformed_media_type_for_renderer():
    assert_raises(SyntaxError, get()._parse_specline, 'media-type')

def test_parse_specline_cant_mistake_malformed_renderer_for_media_type():
    assert_raises(SyntaxError, get()._parse_specline, 'tornado')

def test_parse_specline_enforces_order():
    assert_raises(SyntaxError, get()._parse_specline, 'media/type #!tornado')

def test_parse_specline_obeys_default_by_media_type():
    resource = get()
    resource.website.default_renderers_by_media_type['media/type'] = 'glubber'
    err = assert_raises(ValueError, resource._parse_specline, 'media/type')
    msg = err.args[0]
    assert msg.startswith("Unknown renderer for media/type: glubber."), msg

def test_parse_specline_obeys_default_by_media_type_default():
    resource = get()
    resource.website.default_renderers_by_media_type.default = 'glubber'
    err = assert_raises(ValueError, resource._parse_specline, 'media/type')
    msg = err.args[0]
    assert msg.startswith("Unknown renderer for media/type: glubber."), msg

def test_get_renderer_factory_can_raise_syntax_error():
    resource = get()
    resource.website.default_renderers_by_media_type['media/type'] = 'glubber'
    err = assert_raises( SyntaxError
                       , resource._get_renderer_factory
                       , 'media/type'
                       , 'oo*gle'
                        )
    msg = err.args[0]
    assert msg.startswith("Malformed renderer oo*gle. It must match"
                    " #![a-z0-9.-]+."), msg


# get_response

def get_response(request, response):
    context = { 'request': request
              , 'response': response
               }
    resource = resources.load(request, 0)
    return resource.get_response(context)

NEGOTIATED_RESOURCE = """\
^L
^L text/plain
Greetings, program!
^L text/html
<h1>Greetings, program!</h1>
"""

def test_get_response_gets_response():
    mk(('index', NEGOTIATED_RESOURCE))
    response = Response()
    request = StubRequest.from_fs('index')
    actual = get_response(request, response)
    assert actual is response, actual


def test_get_response_is_happy_not_to_negotiate():
    mk(('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    actual = get_response(request, Response()).body
    assert actual == "Greetings, program!\n", actual

def test_get_response_sets_content_type_when_it_doesnt_negotiate():
    mk(('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    actual = get_response(request, Response()).headers['Content-Type']
    assert actual == "text/plain; charset=UTF-8", actual

def test_get_response_doesnt_reset_content_type_when_not_negotiating():
    mk(('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(request, response).headers['Content-Type']
    assert actual == "never/mind", actual


def test_get_response_negotiates():
    mk(('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    request.headers['Accept'] = 'text/html'
    actual = get_response(request, Response()).body
    assert actual == "<h1>Greetings, program!</h1>\n", actual

def test_get_response_sets_content_type_when_it_negotiates():
    mk(('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    request.headers['Accept'] = 'text/html'
    actual = get_response(request, Response()).headers['Content-Type']
    assert actual == "text/html; charset=UTF-8", actual

def test_get_response_doesnt_reset_content_type_when_negotiating():
    mk(('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    request.headers['Accept'] = 'text/html'
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(request, response).headers['Content-Type']
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(request, response).headers['Content-Type']
    assert actual == "never/mind", actual

def test_get_response_raises_406_if_need_be():
    mk(('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    request.headers['Accept'] = 'cheese/head'
    actual = assert_raises(Response, get_response, request, Response()).code
    assert actual == 406, actual

def test_get_response_406_gives_list_of_acceptable_types():
    mk(('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    request.headers['Accept'] = 'cheese/head'
    actual = assert_raises(Response, get_response, request, Response()).body
    expected ="The following media types are available: text/plain, text/html."
    assert actual == expected, actual

def test_can_override_default_renderers_by_mimetype():
    mk(('.aspen/configure-aspen.py', """\
from aspen.renderers import Renderer, Factory

class Glubber(Renderer):
    def render_content(self, context):
        return "glubber"

class GlubberFactory(Factory):
    Renderer = Glubber

website.renderer_factories['glubber'] = GlubberFactory(website)
website.default_renderers_by_media_type['text/plain'] = 'glubber'

"""), ('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    request.headers['Accept'] = 'text/plain'
    actual = get_response(request, Response()).body
    assert actual == "glubber", actual

def test_can_override_default_renderer_entirely():
    mk(('.aspen/configure-aspen.py', """\
from aspen.renderers import Renderer, Factory

class Glubber(Renderer):
    def render_content(self, context):
        return "glubber"

class GlubberFactory(Factory):
    Renderer = Glubber

website.renderer_factories['glubber'] = GlubberFactory(website)
website.default_renderers_by_media_type.default = 'glubber'

"""), ('index', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index')
    request.headers['Accept'] = 'text/plain'
    actual = get_response(request, Response()).body
    assert actual == "glubber", actual


# indirect

INDIRECTLY_NEGOTIATED_RESOURCE = """\
^L
foo = "program"
^L text/html
<h1>Greetings, {{ foo }}!</h1>
^L text/plain
Greetings, {{ foo }}!"""

def test_indirect_negotiation_sets_media_type():
    mk(('/foo', INDIRECTLY_NEGOTIATED_RESOURCE))
    response = handle('/foo.html')
    expected = "<h1>Greetings, program!</h1>\n"
    actual = response.body
    assert actual == expected, actual

def test_indirect_negotiation_sets_media_type_to_secondary():
    mk(('/foo', INDIRECTLY_NEGOTIATED_RESOURCE))
    response = handle('/foo.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected, actual

def test_indirect_negotiation_with_unsupported_media_type_is_404():
    mk(('/foo', INDIRECTLY_NEGOTIATED_RESOURCE))
    response = handle('/foo.jpg')
    actual = response.code
    assert actual == 404, actual


INDIRECTLY_NEGOTIATED_VIRTUAL_RESOURCE = """\
^L
^L text/html
<h1>Greetings, {{ path['foo'] }}!</h1>
^L text/plain
Greetings, {{ path['foo'] }}!"""


def test_negotiated_inside_virtual_path():
    mk(('/%foo/bar', INDIRECTLY_NEGOTIATED_VIRTUAL_RESOURCE ))
    response = handle('/program/bar.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected, actual


attach_teardown(globals())

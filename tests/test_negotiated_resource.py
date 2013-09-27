from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import resources, Response
from aspen.resources.pagination import Page
from aspen.resources.negotiated_resource import NegotiatedResource
from aspen.testing import assert_raises, teardown_function, handle, mk, StubRequest
from aspen.website import Website
from aspen.renderers.stdlib_template import Factory as TemplateFactory
from aspen.renderers.stdlib_percent import Factory as PercentFactory


def get(**_kw):
    kw = dict( website = Website([])
             , fs = ''
             , raw = '[---]\n[---] text/plain via stdlib_template\n'
             , media_type = ''
             , mtime = 0
              )
    kw.update(_kw)
    return NegotiatedResource(**kw)


def test_negotiated_resource_is_instantiable():
    website = Website([])
    fs = ''
    raw = '[---]\n[---] text/plain via stdlib_template\n'
    media_type = ''
    mtime = 0
    actual = NegotiatedResource(website, fs, raw, media_type, mtime).__class__
    assert actual is NegotiatedResource, actual


# compile_page

def test_compile_page_chokes_on_truly_empty_page():
    assert_raises(SyntaxError, get().compile_page, Page(''))

def test_compile_page_compiles_empty_page():
    page = get().compile_page(Page('', 'text/html'))
    actual = page[0]({}), page[1]
    assert actual == ('', 'text/html'), actual

def test_compile_page_compiles_page():
    page = get().compile_page(Page('foo bar', 'text/html'))
    actual = page[0]({}), page[1]
    assert actual == ('foo bar', 'text/html'), actual


# _parse_specline

def test_parse_specline_parses_specline():
    factory, media_type = get()._parse_specline('media/type via stdlib_template')
    actual = (factory.__class__, media_type)
    assert actual == (TemplateFactory, 'media/type'), actual

def test_parse_specline_doesnt_require_renderer():
    factory, media_type = get()._parse_specline('media/type')
    actual = (factory.__class__, media_type)
    assert actual == (PercentFactory, 'media/type') 

def test_parse_specline_requires_media_type():
    assert_raises(SyntaxError, get()._parse_specline, 'via stdlib_template')

def test_parse_specline_raises_SyntaxError_if_renderer_is_malformed():
    assert_raises(SyntaxError, get()._parse_specline, 'stdlib_template media/type')

def test_parse_specline_raises_SyntaxError_if_media_type_is_malformed():
    assert_raises(SyntaxError, get()._parse_specline, 'media-type via stdlib_template')

def test_parse_specline_cant_mistake_malformed_media_type_for_renderer():
    assert_raises(SyntaxError, get()._parse_specline, 'media-type')

def test_parse_specline_cant_mistake_malformed_renderer_for_media_type():
    assert_raises(SyntaxError, get()._parse_specline, 'stdlib_template')

def test_parse_specline_enforces_order():
    assert_raises(SyntaxError, get()._parse_specline, 'stdlib_template via media/type')

def test_parse_specline_obeys_default_by_media_type():
    resource = get()
    resource.website.default_renderers_by_media_type['media/type'] = 'glubber'
    err = assert_raises(ValueError, resource._parse_specline, 'media/type')
    msg = err.args[0]
    assert msg.startswith("Unknown renderer for media/type: glubber."), msg

def test_parse_specline_obeys_default_by_media_type_default():
    resource = get()
    resource.website.default_renderers_by_media_type.default_factory = lambda: 'glubber'
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
    assert msg.startswith("Malformed renderer oo*gle. It must match"), msg


# get_response

def get_response(request, response):
    context = { 'request': request
              , 'response': response
               }
    resource = resources.load(request, 0)
    return resource.get_response(context)

NEGOTIATED_RESOURCE = """\
[---]
[---] text/plain
Greetings, program!
[---] text/html
<h1>Greetings, program!</h1>
"""

def test_get_response_gets_response():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    response = Response()
    request = StubRequest.from_fs('index.spt')
    actual = get_response(request, response)
    assert actual is response, actual

def test_get_response_is_happy_not_to_negotiate():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    actual = get_response(request, Response()).body
    assert actual == "Greetings, program!\n", actual

def test_get_response_sets_content_type_when_it_doesnt_negotiate():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    actual = get_response(request, Response()).headers['Content-Type']
    assert actual == "text/plain; charset=UTF-8", actual

def test_get_response_doesnt_reset_content_type_when_not_negotiating():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(request, response).headers['Content-Type']
    assert actual == "never/mind", actual


def test_get_response_negotiates():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    request.headers['Accept'] = 'text/html'
    actual = get_response(request, Response()).body
    assert actual == "<h1>Greetings, program!</h1>\n", actual

def test_get_response_sets_content_type_when_it_negotiates():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    request.headers['Accept'] = 'text/html'
    actual = get_response(request, Response()).headers['Content-Type']
    assert actual == "text/html; charset=UTF-8", actual

def test_get_response_doesnt_reset_content_type_when_negotiating():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    request.headers['Accept'] = 'text/html'
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(request, response).headers['Content-Type']
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(request, response).headers['Content-Type']
    assert actual == "never/mind", actual

def test_get_response_raises_406_if_need_be():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    request.headers['Accept'] = 'cheese/head'
    actual = assert_raises(Response, get_response, request, Response()).code
    assert actual == 406, actual

def test_get_response_406_gives_list_of_acceptable_types():
    mk(('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    request.headers['Accept'] = 'cheese/head'
    actual = assert_raises(Response, get_response, request, Response()).body
    expected = "The following media types are available: text/plain, text/html."
    assert actual == expected, actual


OVERRIDE_SIMPLATE = """\
from aspen.renderers import Renderer, Factory

class Glubber(Renderer):
    def render_content(self, context):
        return "glubber"

class GlubberFactory(Factory):
    Renderer = Glubber

website.renderer_factories['glubber'] = GlubberFactory(website)
website.default_renderers_by_media_type['text/plain'] = 'glubber'

"""


def test_can_override_default_renderers_by_mimetype():
    mk(('.aspen/configure-aspen.py', OVERRIDE_SIMPLATE),
       ('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    request.headers['Accept'] = 'text/plain'
    actual = get_response(request, Response()).body
    assert actual == "glubber", actual

def test_can_override_default_renderer_entirely():
    mk(('.aspen/configure-aspen.py', OVERRIDE_SIMPLATE),
       ('index.spt', NEGOTIATED_RESOURCE))
    request = StubRequest.from_fs('index.spt')
    request.headers['Accept'] = 'text/plain'
    actual = get_response(request, Response()).body
    assert actual == "glubber", actual


# indirect

INDIRECTLY_NEGOTIATED_RESOURCE = """\
[-------]
foo = "program"
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/plain
Greetings, %(foo)s!"""

def test_indirect_negotiation_sets_media_type():
    mk(('/foo.spt', INDIRECTLY_NEGOTIATED_RESOURCE))
    response = handle('/foo.html')
    expected = "<h1>Greetings, program!</h1>\n"
    actual = response.body
    assert actual == expected, actual

def test_indirect_negotiation_sets_media_type_to_secondary():
    mk(('/foo.spt', INDIRECTLY_NEGOTIATED_RESOURCE))
    response = handle('/foo.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected, actual

def test_indirect_negotiation_with_unsupported_media_type_is_404():
    mk(('/foo.spt', INDIRECTLY_NEGOTIATED_RESOURCE))
    response = handle('/foo.jpg')
    actual = response.code
    assert actual == 404, actual


INDIRECTLY_NEGOTIATED_VIRTUAL_RESOURCE = """\
[-------]
foo = path['foo']
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/plain
Greetings, %(foo)s!"""


def test_negotiated_inside_virtual_path():
    mk(('/%foo/bar.spt', INDIRECTLY_NEGOTIATED_VIRTUAL_RESOURCE ))
    response = handle('/program/bar.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected, actual

INDIRECTLY_NEGOTIATED_VIRTUAL_RESOURCE_STARTYPE = """\
[-------]
foo = path['foo']
[-------] */*
Unknown request type, %(foo)s!
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/*
Greetings, %(foo)s!"""

def test_negotiated_inside_virtual_path_with_startypes_present():
    mk(('/%foo/bar.spt', INDIRECTLY_NEGOTIATED_VIRTUAL_RESOURCE_STARTYPE ))
    response = handle('/program/bar.html')
    actual = response.body
    assert '<h1>' in actual

def test_negotiated_inside_virtual_path_with_startype_partial_match():
    mk(('/%foo/bar.spt', INDIRECTLY_NEGOTIATED_VIRTUAL_RESOURCE_STARTYPE ))
    response = handle('/program/bar.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected, "got " + repr(actual) + " instead of " + repr(expected)

def test_negotiated_inside_virtual_path_with_startype_fallback():
    mk(('/%foo/bar.spt', INDIRECTLY_NEGOTIATED_VIRTUAL_RESOURCE_STARTYPE ))
    response = handle('/program/bar.jpg')
    expected = "Unknown request type, program!"
    actual = response.body.strip()
    assert actual == expected, "got " + repr(actual) + " instead of " + repr(expected)






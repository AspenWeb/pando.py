from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises, yield_fixture

from aspen import resources, Response
from aspen.resources.pagination import Page
from aspen.resources.simplate import Simplate
from aspen.renderers.stdlib_template import Factory as TemplateFactory
from aspen.renderers.stdlib_percent import Factory as PercentFactory


@yield_fixture
def get(harness):
    def get(**_kw):
        kw = dict( website = harness.client.website
                 , fs = ''
                 , raw = '[---]\n[---] text/plain via stdlib_template\n'
                 , media_type = ''
                 , is_media_type_from_fs=False
                 , mtime = 0
                  )
        kw.update(_kw)
        return Simplate(**kw)
    yield get


def test_unbound_simplate_is_instantiable(harness):
    website = harness.client.website
    fs = ''
    raw = '[---]\n[---] text/plain via stdlib_template\n'
    media_type = ''
    is_media_type_from_fs = False
    mtime = 0
    actual = Simplate(website, fs, raw, media_type, is_media_type_from_fs, mtime).__class__
    assert actual is Simplate


# compile_page

def test_compile_page_chokes_on_truly_empty_page(get):
    raises(SyntaxError, get().compile_page, Page(''))

def test_compile_page_compiles_empty_page(get):
    page = get().compile_page(Page('', 'text/html'))
    actual = page[0]({}), page[1]
    assert actual == ('', 'text/html')

def test_compile_page_compiles_page(get):
    page = get().compile_page(Page('foo bar', 'text/html'))
    actual = page[0]({}), page[1]
    assert actual == ('foo bar', 'text/html')


# _parse_specline

def test_parse_specline_parses_specline(get):
    factory, media_type = get()._unbound_parse_specline('media/type via stdlib_template')
    actual = (factory.__class__, media_type)
    assert actual == (TemplateFactory, 'media/type')

def test_parse_specline_doesnt_require_renderer(get):
    factory, media_type = get()._unbound_parse_specline('media/type')
    actual = (factory.__class__, media_type)
    assert actual == (PercentFactory, 'media/type')

def test_parse_specline_requires_media_type(get):
    raises(SyntaxError, get()._unbound_parse_specline, 'via stdlib_template')

def test_parse_specline_raises_SyntaxError_if_renderer_is_malformed(get):
    raises(SyntaxError, get()._unbound_parse_specline, 'stdlib_template media/type')

def test_parse_specline_raises_SyntaxError_if_media_type_is_malformed(get):
    raises(SyntaxError, get()._unbound_parse_specline, 'media-type via stdlib_template')

def test_parse_specline_cant_mistake_malformed_media_type_for_renderer(get):
    raises(SyntaxError, get()._unbound_parse_specline, 'media-type')

def test_parse_specline_cant_mistake_malformed_renderer_for_media_type(get):
    raises(SyntaxError, get()._unbound_parse_specline, 'stdlib_template')

def test_parse_specline_enforces_order(get):
    raises(SyntaxError, get()._unbound_parse_specline, 'stdlib_template via media/type')

def test_parse_specline_obeys_default_by_media_type(get):
    resource = get()
    resource.website.default_renderers_by_media_type['media/type'] = 'glubber'
    err = raises(ValueError, resource._unbound_parse_specline, 'media/type').value
    msg = err.args[0]
    assert msg.startswith("Unknown renderer for media/type: glubber."), msg

def test_parse_specline_obeys_default_by_media_type_default(get):
    resource = get()
    resource.website.default_renderers_by_media_type.default_factory = lambda: 'glubber'
    err = raises(ValueError, resource._unbound_parse_specline, 'media/type').value
    msg = err.args[0]
    assert msg.startswith("Unknown renderer for media/type: glubber.")

def test_get_renderer_factory_can_raise_syntax_error(get):
    resource = get()
    resource.website.default_renderers_by_media_type['media/type'] = 'glubber'
    err = raises( SyntaxError
                       , resource._get_renderer_factory
                       , 'media/type'
                       , 'oo*gle'
                        ).value
    msg = err.args[0]
    assert msg.startswith("Malformed renderer oo*gle. It must match")


# get_response

def get_state(harness, *a, **kw):
    kw['return_after'] = 'dispatch_request_to_filesystem'
    kw['want'] = 'state'
    return harness.simple(*a, **kw)

def get_response(state, response):
    context = { 'request': state['request']
              , 'dispatch_result': state['dispatch_result']
              , 'response': response
               }
    resource = resources.load(state['website'], state['dispatch_result'].match, 0)
    return resource.get_response(context)

UNBOUND_SIMPLATE = """\
[---]
[---] text/plain
Greetings, program!
[---] text/html
<h1>Greetings, program!</h1>
"""

def test_get_response_gets_response(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    response = Response()
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    actual = get_response(state, response)
    assert actual is response

def test_get_response_is_happy_not_to_negotiate(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    actual = get_response(state, Response()).body
    assert actual == "Greetings, program!\n"

def test_get_response_sets_content_type_when_it_doesnt_negotiate(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    actual = get_response(state, Response()).headers['Content-Type']
    assert actual == "text/plain; charset=UTF-8"

def test_get_response_doesnt_reset_content_type_when_not_negotiating(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(state, response).headers['Content-Type']
    assert actual == "never/mind"

def test_get_response_negotiates(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    state['request'].headers['Accept'] = 'text/html'
    actual = get_response(state, Response()).body
    assert actual == "<h1>Greetings, program!</h1>\n"

def test_handles_busted_accept(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    # Set an invalid Accept header so it will return default (text/plain)
    state['request'].headers['Accept'] = 'text/html;'
    actual = get_response(state, Response()).body
    assert actual == "Greetings, program!\n"

def test_get_response_sets_content_type_when_it_negotiates(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    state['request'].headers['Accept'] = 'text/html'
    actual = get_response(state, Response()).headers['Content-Type']
    assert actual == "text/html; charset=UTF-8"

def test_get_response_doesnt_reset_content_type_when_negotiating(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    state['request'].headers['Accept'] = 'text/html'
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(state, response).headers['Content-Type']
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(state, response).headers['Content-Type']
    assert actual == "never/mind"

def test_get_response_raises_406_if_need_be(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    state['request'].headers['Accept'] = 'cheese/head'
    actual = raises(Response, get_response, state, Response()).value.code
    assert actual == 406

def test_get_response_406_gives_list_of_acceptable_types(harness):
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    state['request'].headers['Accept'] = 'cheese/head'
    actual = raises(Response, get_response, state, Response()).value.body
    expected = "The following media types are available: text/plain, text/html."
    assert actual == expected


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


def test_can_override_default_renderers_by_mimetype(harness):
    harness.fs.project.mk(('configure-aspen.py', OVERRIDE_SIMPLATE),)
    harness.fs.www.mk(('index.spt', UNBOUND_SIMPLATE),)
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    state['request'].headers['Accept'] = 'text/plain'
    actual = get_response(state, Response()).body
    assert actual == "glubber"

def test_can_override_default_renderer_entirely(harness):
    harness.fs.project.mk(('configure-aspen.py', OVERRIDE_SIMPLATE))
    state = get_state(harness, filepath='index.spt', contents=UNBOUND_SIMPLATE)
    state['request'].headers['Accept'] = 'text/plain'
    actual = get_response(state, Response()).body
    assert actual == "glubber"


# indirect

INDIRECTLY_NEGOTIATED_UNBOUND_SIMPLATE = """\
[-------]
foo = "program"
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/plain
Greetings, %(foo)s!"""

def test_indirect_negotiation_sets_media_type(harness):
    harness.fs.www.mk(('/foo.spt', INDIRECTLY_NEGOTIATED_UNBOUND_SIMPLATE))
    response = harness.client.GET('/foo.html')
    expected = "<h1>Greetings, program!</h1>\n"
    actual = response.body
    assert actual == expected

def test_indirect_negotiation_sets_media_type_to_secondary(harness):
    harness.fs.www.mk(('/foo.spt', INDIRECTLY_NEGOTIATED_UNBOUND_SIMPLATE))
    response = harness.client.GET('/foo.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected

def test_indirect_negotiation_with_unsupported_media_type_is_404(harness):
    harness.fs.www.mk(('/foo.spt', INDIRECTLY_NEGOTIATED_UNBOUND_SIMPLATE))
    response = harness.client.GxT('/foo.jpg')
    assert response.code == 404


UNBOUND_SIMPLATE_VIRTUAL_PATH = """\
[-------]
foo = path['foo']
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/plain
Greetings, %(foo)s!"""


def test_unbound_inside_virtual_path(harness):
    harness.fs.www.mk(('/%foo/bar.spt', UNBOUND_SIMPLATE_VIRTUAL_PATH ))
    response = harness.client.GET('/program/bar.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected

UNBOUND_SIMPLATE_STARTYPE = """\
[-------]
foo = path['foo']
[-------] */*
Unknown request type, %(foo)s!
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/*
Greetings, %(foo)s!"""

def test_unbound_inside_virtual_path_with_startypes_present(harness):
    harness.fs.www.mk(('/%foo/bar.spt', UNBOUND_SIMPLATE_STARTYPE ))
    response = harness.client.GET('/program/bar.html')
    actual = response.body
    assert '<h1>' in actual

def test_unbound_inside_virtual_path_with_startype_partial_match(harness):
    harness.fs.www.mk(('/%foo/bar.spt', UNBOUND_SIMPLATE_STARTYPE ))
    response = harness.client.GET('/program/bar.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected

def test_unbound_inside_virtual_path_with_startype_fallback(harness):
    harness.fs.www.mk(('/%foo/bar.spt', UNBOUND_SIMPLATE_STARTYPE ))
    response = harness.client.GET('/program/bar.jpg')
    expected = "Unknown request type, program!"
    actual = response.body.strip()
    assert actual == expected

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises, yield_fixture

from aspen import resources
from aspen.http.resource import Dynamic
from aspen.output import Output
from aspen.pagination import Page
from aspen.request_processor import dispatcher
from aspen.renderers.stdlib_template import Factory as TemplateFactory
from aspen.renderers.stdlib_percent import Factory as PercentFactory


@yield_fixture
def get(harness):
    def get(**_kw):
        kw = dict( request_processor = harness.request_processor
                 , fs = ''
                 , raw = b'[---]\n[---] text/plain via stdlib_template\n'
                 , default_media_type = ''
                  )
        kw.update(_kw)
        return Dynamic(**kw)
    yield get


def test_dynamic_resource_is_instantiable(harness):
    request_processor = harness.request_processor
    fs = ''
    raw = b'[---]\n[---] text/plain via stdlib_template\n'
    media_type = ''
    actual = Dynamic(request_processor, fs, raw, media_type).__class__
    assert actual is Dynamic


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
    factory, media_type = get()._parse_specline('media/type via stdlib_template')
    actual = (factory.__class__, media_type)
    assert actual == (TemplateFactory, 'media/type')

def test_parse_specline_doesnt_require_renderer(get):
    factory, media_type = get()._parse_specline('media/type')
    actual = (factory.__class__, media_type)
    assert actual == (PercentFactory, 'media/type')

def test_parse_specline_requires_media_type(get):
    raises(SyntaxError, get()._parse_specline, 'via stdlib_template')

def test_parse_specline_raises_SyntaxError_if_renderer_is_malformed(get):
    raises(SyntaxError, get()._parse_specline, 'stdlib_template media/type')

def test_parse_specline_raises_SyntaxError_if_media_type_is_malformed(get):
    raises(SyntaxError, get()._parse_specline, 'media-type via stdlib_template')

def test_parse_specline_cant_mistake_malformed_media_type_for_renderer(get):
    raises(SyntaxError, get()._parse_specline, 'media-type')

def test_parse_specline_cant_mistake_malformed_renderer_for_media_type(get):
    raises(SyntaxError, get()._parse_specline, 'stdlib_template')

def test_parse_specline_enforces_order(get):
    raises(SyntaxError, get()._parse_specline, 'stdlib_template via media/type')

def test_parse_specline_obeys_default_by_media_type(get):
    resource = get()
    resource.request_processor.default_renderers_by_media_type['media/type'] = 'glubber'
    err = raises(ValueError, resource._parse_specline, 'media/type').value
    msg = err.args[0]
    assert msg.startswith("Unknown renderer for media/type: glubber."), msg

def test_parse_specline_obeys_default_by_media_type_default(get):
    resource = get()
    resource.request_processor.default_renderers_by_media_type.default_factory = lambda: 'glubber'
    err = raises(ValueError, resource._parse_specline, 'media/type').value
    msg = err.args[0]
    assert msg.startswith("Unknown renderer for media/type: glubber.")

def test_get_renderer_factory_can_raise_syntax_error(get):
    resource = get()
    resource.request_processor.default_renderers_by_media_type['media/type'] = 'glubber'
    err = raises( SyntaxError
                       , resource._get_renderer_factory
                       , 'media/type'
                       , 'oo*gle'
                        ).value
    msg = err.args[0]
    assert msg.startswith("Malformed renderer oo*gle. It must match")


# render

def _get_state(harness, *a, **kw):
    kw['return_after'] = 'dispatch_path_to_filesystem'
    kw['want'] = 'state'
    return harness.simple(*a, **kw)


def _render(state):
    resource = resources.load(state['request_processor'], state['dispatch_result'].match, 0)
    state['resource'] = resource
    state['output'] = state.get('output', Output())
    return resource.render(state)

SIMPLATE = """\
[---]
[---] text/plain
Greetings, program!
[---] text/html
<h1>Greetings, program!</h1>
"""

def test_render_renders(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    output = Output()
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['output'] = output
    actual = _render(state)
    assert actual is output

def test_render_is_happy_not_to_negotiate(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    actual = _render(state).body
    assert actual == "Greetings, program!\n"

def test_render_sets_media_type_when_it_doesnt_negotiate(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    output = _render(state)
    assert output.media_type == "text/plain"
    assert output.charset is None

def test_render_doesnt_reset_media_type_when_not_negotiating(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    output = Output()
    output.media_type = 'never/mind'
    state['output'] =output
    actual = _render(state).media_type
    assert actual == "never/mind"

def test_render_is_happy_not_to_negotiate_with_defaults(harness):
    harness.fs.www.mk(('index.spt', '''[---]\n[---]\nGreetings, program!\n'''))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    actual = _render(state).body
    assert actual == "Greetings, program!\n"

def test_render_negotiates(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['accept_header'] = 'text/html'
    actual = _render(state).body
    assert actual == "<h1>Greetings, program!</h1>\n"

def test_handles_busted_accept(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['accept_header'] = 'text/html;'
    actual = _render(state).body
    assert actual == "Greetings, program!\n"

def test_render_sets_media_type_when_it_negotiates(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['accept_header'] = 'text/html'
    output = _render(state)
    assert output.media_type == "text/html"
    assert output.charset is None

def test_render_doesnt_reset_media_type_when_negotiating(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['accept_header'] = 'text/html'
    output = Output()
    output.media_type = 'never/mind'
    state['output'] = output
    actual = _render(state).media_type
    output = Output()
    output.media_type = 'never/mind'
    state['output'] = output
    actual = _render(state).media_type
    assert actual == "never/mind"

def test_render_raises_if_direct_negotiation_fails(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['accept_header'] = 'cheese/head'
    raises(dispatcher.DirectNegotiationFailure, _render, state)

def test_render_negotation_failures_include_available_types(harness):
    harness.fs.www.mk(('index.spt', SIMPLATE))
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['accept_header'] = 'cheese/head'
    actual = raises(dispatcher.DirectNegotiationFailure, _render, state).value.message
    expected = "Couldn't satisfy cheese/head. The following media types are available: " \
               "text/plain, text/html."
    assert actual == expected


from aspen.renderers import Renderer, Factory

class Glubber(Renderer):
    def render_content(self, context):
        return "glubber"

class GlubberFactory(Factory):
    Renderer = Glubber

def install_glubber(harness):
    harness.request_processor.renderer_factories['glubber'] = \
                                                          GlubberFactory(harness.request_processor)
    harness.request_processor.default_renderers_by_media_type['text/plain'] = 'glubber'

def test_can_override_default_renderers_by_mimetype(harness):
    install_glubber(harness)
    harness.fs.www.mk(('index.spt', SIMPLATE),)
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['accept_header'] = 'text/plain'
    actual = _render(state).body
    assert actual == "glubber"

def test_can_override_default_renderer_entirely(harness):
    install_glubber(harness)
    state = _get_state(harness, filepath='index.spt', contents=SIMPLATE)
    state['accept_header'] = 'text/plain'
    actual = _render(state).body
    assert actual == "glubber"


# indirect

INDIRECTLY_NEGOTIATED_SIMPLATE = """\
[-------]
foo = "program"
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/plain
Greetings, %(foo)s!"""

def test_indirect_negotiation_sets_media_type(harness):
    response = harness.simple(INDIRECTLY_NEGOTIATED_SIMPLATE, '/foo.spt', '/foo.html')
    expected = "<h1>Greetings, program!</h1>\n"
    actual = response.body
    assert actual == expected

def test_indirect_negotiation_sets_media_type_to_secondary(harness):
    response = harness.simple(INDIRECTLY_NEGOTIATED_SIMPLATE, '/foo.spt', '/foo.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected

def test_indirect_negotiation_with_unsupported_media_type_is_an_error(harness):
    with raises(dispatcher.IndirectNegotiationFailure):
        harness.simple(INDIRECTLY_NEGOTIATED_SIMPLATE, '/foo.spt', '/foo.jpg')


SIMPLATE_VIRTUAL_PATH = """\
[-------]
foo = path['foo']
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/plain
Greetings, %(foo)s!"""


def test_dynamic_resource_inside_virtual_path(harness):
    response = harness.simple(SIMPLATE_VIRTUAL_PATH, '/%foo/bar.spt', '/program/bar.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected

SIMPLATE_STARTYPE = """\
[-------]
foo = path['foo']
[-------] */*
Unknown request type, %(foo)s!
[-------] text/html
<h1>Greetings, %(foo)s!</h1>
[-------] text/*
Greetings, %(foo)s!"""

def test_dynamic_resource_inside_virtual_path_with_startypes_present(harness):
    response = harness.simple(SIMPLATE_STARTYPE, '/%foo/bar.spt', '/program/bar.html')
    actual = response.body
    assert '<h1>' in actual

def test_dynamic_resource_inside_virtual_path_with_startype_partial_match(harness):
    response = harness.simple(SIMPLATE_STARTYPE, '/%foo/bar.spt', '/program/bar.txt')
    expected = "Greetings, program!"
    actual = response.body
    assert actual == expected

def test_dynamic_resource_inside_virtual_path_with_startype_fallback(harness):
    response = harness.simple(SIMPLATE_STARTYPE, '/%foo/bar.spt', '/program/bar.jpg')
    expected = "Unknown request type, program!"
    actual = response.body.strip()
    assert actual == expected

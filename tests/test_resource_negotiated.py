from aspen import Response
from aspen.http.request import Request
from aspen.resources.negotiated_resource import NegotiatedResource
from aspen.testing import assert_raises, attach_teardown, mk
from aspen.website import Website


def get(**_kw):
    kw = dict( website = Website([])
                   , fs = ''
                   , raw = '^L^L'
                   , mimetype = ''
                   , modtime = 0
                    )
    kw.update(_kw)
    return NegotiatedResource(**kw)


def test_negotiated_resource_is_instantiable():
    website = Website([])
    fs = ''
    raw = '^L^L'
    mimetype = ''
    modtime = 0
    actual = NegotiatedResource(website, fs, raw, mimetype, modtime).__class__
    assert actual is NegotiatedResource, actual


# compile_page

def test_compile_page_compiles_empty_page():
    page = get().compile_page('', '')
    actual = page[0], page[1]()
    assert actual == ('text/plain', ''), actual

def test_compile_page_compiles_page():
    page = get().compile_page('foo bar', '')
    actual = page[0], page[1]()
    assert actual == ('text/plain', 'foo bar'), actual


# _parse_specline

def test_parse_specline_parses_specline():
    actual = get()._parse_specline('#!renderer media/type')
    assert actual == ('renderer', 'media/type'), actual

def test_parse_specline_doesnt_require_renderer():
    actual = get()._parse_specline('media/type')
    assert actual == (None, 'media/type'), actual

def test_parse_specline_doesnt_require_media_type():
    actual = get()._parse_specline('#!renderer')
    assert actual == ('renderer', None), actual

def test_parse_specline_raises_SyntaxError_if_renderer_is_malformed():
    assert_raises(SyntaxError, get()._parse_specline, 'renderer media/type')

def test_parse_specline_raises_SyntaxError_if_media_type_is_malformed():
    assert_raises(SyntaxError, get()._parse_specline, '#!renderer media-type')

def test_parse_specline_cant_mistake_malformed_media_type_for_renderer():
    assert_raises(SyntaxError, get()._parse_specline, 'media-type')

def test_parse_specline_cant_mistake_malformed_renderer_for_media_type():
    assert_raises(SyntaxError, get()._parse_specline, 'renderer')

def test_parse_specline_enforces_order():
    assert_raises(SyntaxError, get()._parse_specline, 'media/type #!renderer')


# get_response

def get_response(request, response):
    namespace = { 'request': request
                , 'response': response
                 }
    return get().get_response(namespace)

NEGOTIATED_RESOURCE = """\
^L text/plain
Greetings, program!
^L text/html
<h1>Greetings, program!</h1>
"""

def test_get_response_gets_response():
    response = Response()
    actual = get_response(Request(), response)
    assert actual is response, actual


def test_get_response_is_happy_not_to_negotiate():
    mk(('index', NEGOTIATED_RESOURCE))
    request = Request()
    actual = get_response(request, Response()).body
    assert actual == "Greetings, program!", actual

def test_get_response_sets_content_type_when_it_doesnt_negotiate():
    mk(('index', NEGOTIATED_RESOURCE))
    actual = get_response(Request(), Response()).headers['Content-Type']
    assert actual == "text/plain", actual

def test_get_response_doesnt_reset_content_type_when_not_negotiating():
    mk(('index', NEGOTIATED_RESOURCE))
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(Request(), response).headers['Content-Type']
    assert actual == "never/mind", actual


def test_get_response_negotiates():
    mk(('index', NEGOTIATED_RESOURCE))
    request = Request()
    request.headers['Accept'] = 'text/html'
    actual = get_response(request, Response()).body
    assert actual == "<h1>Greetings, program!</h1>", actual

def test_get_response_sets_content_type_when_it_negotiates():
    mk(('index', NEGOTIATED_RESOURCE))
    request = Request()
    request.headers['Accept'] = 'text/html'
    actual = get_response(request, Response()).headers['Content-Type']
    assert actual == "text/html", actual

def test_get_response_doesnt_reset_content_type_when_negotiating():
    mk(('index', NEGOTIATED_RESOURCE))
    request = Request()
    request.headers['Accept'] = 'text/html'
    response = Response()
    response.headers['Content-Type'] = 'never/mind'
    actual = get_response(request, response).headers['Content-Type']
    assert actual == "never/mind", actual


attach_teardown(globals())

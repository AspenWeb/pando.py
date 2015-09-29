# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.simplates import _decode
from pytest import raises


def test_default_media_type_works(harness):
    harness.fs.www.mk(('index.spt', """
[---]
[---]
plaintext"""))
    response = harness.client.GET(raise_immediately=False)
    assert "plaintext" in response.body

SIMPLATE="""
foo = %s
[---] via stdlib_format
{foo}"""

def test_can_use_request_headers(harness):
    response = harness.simple( SIMPLATE % "request.headers['Foo']"
                             , HTTP_FOO=b'bar'
                              )
    assert response.body == 'bar'


def test_can_use_request_cookie(harness):
    response = harness.simple( SIMPLATE % "request.cookie['foo'].value"
                             , HTTP_COOKIE=b'foo=bar'
                              )
    assert response.body == 'bar'


def test_can_use_request_path(harness):
    response = harness.simple( SIMPLATE % "request.path.raw"
                              )
    assert response.body == '/'


def test_can_use_request_qs(harness):
    response = harness.simple( SIMPLATE % "request.qs['foo']"
                             , uripath='/?foo=bloo'
                              )
    assert response.body == 'bloo'


def test_can_use_request_method(harness):
    response = harness.simple( SIMPLATE % "request.method"
                             , uripath='/?foo=bloo'
                              )
    assert response.body == 'GET'


def test_cant_implicitly_override_state(harness):
    state = harness.simple("[---]\n"
        "resource = 'foo'\n"
        "[---] via stdlib_format\n"
        "{resource}",
        want='state'
    )
    assert state['response'].body == 'foo'
    assert state['resource'] != 'foo'


def test_can_explicitly_override_state(harness):
    response = harness.simple("[---]\n"
        "from aspen import Response\n"
        "state['response'] = Response(299)\n"
        "[---]\n"
        "bar"
    )
    assert response.code == 299
    assert response.body == 'bar'


def test_but_python_sections_exhibit_module_scoping_behavior(harness):
    response = harness.simple("""[---]
bar = 'baz'
def foo():
    return bar
foo = foo()
[---] text/html via stdlib_format
{foo}""")
    assert response.body == 'baz'


def test_one_page_works(harness):
    response = harness.simple("Template")
    assert response.body == 'Template'


def test_two_pages_works(harness):
    response = harness.simple(SIMPLATE % "'Template'")
    assert response.body == 'Template'


def test_three_pages_one_python_works(harness):
    response = harness.simple("""
foo = 'Template'
[---] text/plain via stdlib_format
{foo}
[---] text/xml
<foo>{foo}</foo>""")
    assert response.body.strip() == 'Template'


def test_three_pages_two_python_works(harness):
    response = harness.simple("""[---]
python_code = True
[---]
Template""")
    assert response.body == 'Template'


# _decode

def test_decode_can_take_encoding_from_first_line():
    actual = _decode(b"""\
    # -*- coding: utf8 -*-
    text = u'א'
    """)
    expected = """\
    # encoding set to utf8
    text = u'א'
    """
    assert actual == expected

def test_decode_can_take_encoding_from_second_line():
    actual = _decode(b"""\
    #!/blah/blah
    # -*- coding: utf8 -*-
    text = u'א'
    """)
    expected = """\
    #!/blah/blah
    # encoding set to utf8
    text = u'א'
    """
    assert actual == expected

def test_decode_prefers_first_line_to_second():
    actual = _decode(b"""\
    # -*- coding: utf8 -*-
    # -*- coding: ascii -*-
    text = u'א'
    """)
    expected = """\
    # encoding set to utf8
    # encoding NOT set to ascii
    text = u'א'
    """
    assert actual == expected

def test_decode_ignores_third_line():
    actual = _decode(b"""\
    # -*- coding: utf8 -*-
    # -*- coding: ascii -*-
    # -*- coding: cornnuts -*-
    text = u'א'
    """)
    expected = """\
    # encoding set to utf8
    # encoding NOT set to ascii
    # -*- coding: cornnuts -*-
    text = u'א'
    """
    assert actual == expected

def test_decode_can_take_encoding_from_various_line_formats():
    formats = [ b'-*- coding: utf8 -*-'
              , b'-*- encoding: utf8 -*-'
              , b'coding: utf8'
              , b'  coding: utf8'
              , b'\tencoding: utf8'
              , b'\t flubcoding=utf8'
               ]
    for fmt in formats:
        def test():
            actual = _decode(b"""\
            # {0}
            text = u'א'
            """.format(fmt))
            expected = """\
            # encoding set to utf8
            text = u'א'
            """
            assert actual == expected
        yield test

def test_decode_cant_take_encoding_from_bad_line_formats():
    formats = [ b'-*- coding : utf8 -*-'
              , b'foo = 0 -*- encoding: utf8 -*-'
              , b'  coding : utf8'
              , b'encoding : utf8'
              , b'  flubcoding =utf8'
              , b'coding: '
               ]
    for fmt in formats:
        def test():
            raw = b"""\
            # {0}
            text = u'א'
            """.format(fmt)
            raises(UnicodeDecodeError, _decode, raw)
        yield test

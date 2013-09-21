from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from textwrap import dedent

from aspen import Response
from aspen.testing import assert_raises, check, handle
from aspen.testing.fsfix import attach_teardown, mk
from aspen.resources.pagination import split


# Tests
# =====

def test_barely_working():
    response = check("Greetings, program!", 'index.html', False)

    expected = 'text/html'
    actual = response.headers['Content-Type']
    assert actual == expected, actual

def test_charset_static_barely_working():
    response = check( "Greetings, program!", 'index.html', False
                    , argv=['--charset_static=OOG']
                     )
    expected = 'text/html; charset=OOG'
    actual = response.headers['Content-Type']
    assert actual == expected, actual

def test_charset_dynamic_barely_working():
    response = check( "[---]\nGreetings, program!", 'index.html.spt', False
                    , argv=['--charset_dynamic=CHEESECODE']
                     )
    expected = 'text/html; charset=CHEESECODE'
    actual = response.headers['Content-Type']
    assert actual == expected, actual

def test_resource_pages_work():
    expected = "Greetings, bar!"
    actual = check("foo = 'bar'\n[--------]\nGreetings, %(foo)s!")
    assert actual == expected, actual

def test_resource_dunder_all_limits_vars():
    actual = assert_raises( KeyError
                            , check
                            , "foo = 'bar'\n"
                              "__all__ = []\n"
                              "[---------]\n"
                              "Greetings, %(foo)s!"
                             )
    # in production, KeyError is turned into a 500 by an outer wrapper
    assert type(actual) == KeyError, actual

def test_path_part_params_are_available():
    mk(('/foo/index.html.spt', """
if 'b' in path.parts[0].params:
    a = path.parts[0].params['a']
[---]
%(a)s"""))
    expected = "3"
    actual = handle('/foo;a=1;b;a=3/').body
    assert actual == expected, actual + " isn't " + expected

def test_utf8():
    expected = unichr(1758).encode('utf8')
    expected = unichr(1758)
    actual = check("""
"#empty first page"
[------------------]
text = unichr(1758)
[------------------]
%(text)s
    """).strip()
    assert actual == expected, repr(actual) + " != expected " + repr(expected)

def test_resources_dont_leak_whitespace():
    """This aims to resolve https://github.com/whit537/aspen/issues/8.
    """
    actual = check(dedent("""
        [--------------]
        foo = [1,2,3,4]
        [--------------]
        %(foo)r"""))
    expected = "[1, 2, 3, 4]"
    assert actual == expected, repr(actual)

def test_negotiated_resource_doesnt_break():
    expected = "Greetings, bar!\n"
    actual = check("""
[-----------]
foo = 'bar'
[-----------] text/plain
Greetings, %(foo)s!
[-----------] text/html
<h1>Greetings, %(foo)s!</h1>
"""
, filename='index.spt')
    assert actual == expected, actual


# Unicode example in the /templating/ doc.
# ========================================
# See also: https://github.com/whit537/aspen/issues/10

eg = """
latinate = chr(181).decode('latin1')
response.headers['Content-Type'] = 'text/plain; charset=latin1'
r = latinate.encode('latin1')
[-------------------------------------]
 %(r)s"""

def test_content_type_is_right_in_template_doc_unicode_example():
    response = check(eg, body=False)
    expected = "text/plain; charset=latin1"
    actual = response.headers['Content-Type']
    assert actual == expected, actual

def test_body_is_right_in_template_doc_unicode_example():
    expected = chr(181)
    actual = check(eg).strip()
    assert actual == expected, actual


# raise Response
# ==============

def test_raise_response_works():
    expected = 404
    response = assert_raises( Response
                            , check
                            , "from aspen import Response\n"
                              "raise Response(404)\n"
                              "[---------]\n"
                             )
    actual = response.code
    assert actual == expected, actual

def test_exception_location_preserved_for_response_raised_in_page_2():
    # https://github.com/gittip/aspen-python/issues/153
    expected = ('index.html.spt', 1)
    try: check("from aspen import Response; raise Response(404)\n[---]\n")
    except Response, response: actual = response.whence_raised()
    assert actual == expected, actual

def test_website_is_in_context():
    expected = "It worked."
    actual = check("""
assert website.__class__.__name__ == 'Website', website
[--------]
[--------]
It worked.""")
    assert actual == expected, actual

def test_unknown_mimetype_yields_default_mimetype():
    response = check( "Greetings, program!"
                    , body=False
                    , filename="foo.flugbaggity"
                     )
    expected = "text/plain"
    actual = response.headers['Content-Type']
    assert actual == expected, actual

def test_templating_without_script_works():
    response = Response()
    expected = "index.html"

    # I want a slash on the front of index.html but it's an artifact of
    # StubRequest that we don't get one.

    actual = check("[-----] via stdlib_format\n{request.line.uri.path.raw}", response=response)
    assert actual == expected, actual


# Test offset calculation

def check_offsets(raw, offsets):
    actual = [page.offset for page in split(raw)]
    assert actual == offsets, actual

def test_offset_calculation_basic():
    check_offsets('\n\n\n[---]\n\n', [0, 4])

def test_offset_calculation_for_empty_file():
    check_offsets('', [0])

def test_offset_calculation_advanced():
    raw = (
        '\n\n\n[---]\n'
        'cheese\n[---]\n'
        '\n\n\n\n\n\n[---]\n'
        'Monkey\nHead\n') #Be careful: this is implicit concation, not a tuple
    check_offsets(raw, [0, 4, 6, 13])



# Teardown
# ========

attach_teardown(globals())

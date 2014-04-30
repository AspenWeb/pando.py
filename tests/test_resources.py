# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from aspen import Response
from aspen.resources.pagination import split
from pytest import raises


# Tests
# =====

def test_barely_working(harness):
    response = harness.simple('Greetings, program!', 'index.html')

    expected = 'text/html'
    actual = response.headers['Content-Type']
    assert actual == expected

def test_load_resource_loads_resource(harness):
    harness.fs.www.mk(('/index.html.spt', 'bar=0\n[---]\n[---]'))
    resource = harness.client.load_resource('/')
    assert resource.pages[0]['bar'] == 0

def test_charset_static_barely_working(harness):
    response = harness.simple( 'Greetings, program!'
                             , 'index.html'
                             , argv=['--charset_static', 'OOG']
                              )
    expected = 'text/html; charset=OOG'
    actual = response.headers['Content-Type']
    assert actual == expected

def test_charset_dynamic_barely_working(harness):
    response = harness.simple( '[---]\nGreetings, program!'
                             , 'index.html.spt'
                             , argv=['--charset_dynamic', 'CHEESECODE']
                              )
    expected = 'text/html; charset=CHEESECODE'
    actual = response.headers['Content-Type']
    assert actual == expected

def test_resource_pages_work(harness):
    actual = harness.simple("foo = 'bar'\n[--------]\nGreetings, %(foo)s!").body
    assert actual == "Greetings, bar!"

def test_resource_dunder_all_limits_vars(harness):
    actual = raises( KeyError
                            , harness.simple
                            , "foo = 'bar'\n"
                              "__all__ = []\n"
                              "[---------]\n"
                              "Greetings, %(foo)s!"
                             ).value
    # in production, KeyError is turned into a 500 by an outer wrapper
    assert type(actual) == KeyError

def test_path_part_params_are_available(harness):
    response = harness.simple("""
        if 'b' in path.parts[0].params:
            a = path.parts[0].params['a']
        [---]
        %(a)s
    """, '/foo/index.html.spt', '/foo;a=1;b;a=3/')
    assert response.body == "3\n"

def test_utf8(harness):
    expected = unichr(1758)
    actual = harness.simple("""
        "#empty first page"
        [------------------]
        text = unichr(1758)
        [------------------]
        %(text)s
    """).body.strip()
    assert actual == expected

def test_utf8_char(harness):
    expected = u'א'
    actual = harness.simple(b"""
        # encoding=utf8
        "#empty first page"
        [------------------]
        text = u'א'
        [------------------]
        %(text)s
    """).body.strip()
    assert actual == expected

def test_resources_dont_leak_whitespace(harness):
    """This aims to resolve https://github.com/whit537/aspen/issues/8.
    """
    actual = harness.simple("""
        [--------------]
        foo = [1,2,3,4]
        [--------------]
        %(foo)r""").body
    assert actual == "[1, 2, 3, 4]"

def test_negotiated_resource_doesnt_break(harness):
    expected = "Greetings, bar!\n"
    actual = harness.simple("""
        [-----------]
        foo = 'bar'
        [-----------] text/plain
        Greetings, %(foo)s!
        [-----------] text/html
        <h1>Greetings, %(foo)s!</h1>
        """
        , filepath='index.spt').body
    assert actual == expected

# non-ascii/unicode testing

eg = b"""
latinate = chr(181).decode('latin1')
response.headers['Content-Type'] = 'text/plain; charset=latin1'
r = latinate
[-------------------------------------]
 %(r)s"""

def test_content_type_is_right_in_template_doc_unicode_example(harness):
    assert harness.simple(eg).headers['Content-Type'] == "text/plain; charset=latin1"

def test_body_is_right_in_template_doc_unicode_example(harness):
    assert harness.simple(eg).body.strip() == unichr(181)


# raise Response
# ==============

def test_raise_response_works(harness):
    expected = 404
    response = raises( Response
                            , harness.simple
                            , "from aspen import Response\n"
                              "raise Response(404)\n"
                              "[---------]\n"
                             ).value
    actual = response.code
    assert actual == expected

def test_exception_location_preserved_for_response_raised_in_page_2(harness):
    # https://github.com/gittip/aspen-python/issues/153
    expected_path = os.path.join(os.path.basename(harness.fs.www.root), 'index.html.spt')
    expected = (expected_path, 1)
    try:
        harness.simple('from aspen import Response; raise Response(404)\n[---]\n')
    except Response, response:
        actual = response.whence_raised()
    assert actual == expected

def test_website_is_in_context(harness):
    response = harness.simple("""
        assert website.__class__.__name__ == 'Website', website
        [--------]
        [--------]
        It worked.""")
    assert response.body == 'It worked.'

def test_unknown_mimetype_yields_default_mimetype(harness):
    response = harness.simple( 'Greetings, program!'
                             , filepath='foo.flugbaggity'
                              )
    assert response.headers['Content-Type'] == 'text/plain'

def test_templating_without_script_works(harness):
    response = harness.simple('[-----] via stdlib_format\n{request.line.uri.path.raw}')
    assert response.body == '/'


# Test offset calculation

def check_offsets(raw, offsets):
    actual = [page.offset for page in split(raw)]
    assert actual == offsets

def test_offset_calculation_basic(harness):
    check_offsets('\n\n\n[---]\n\n', [0, 4])

def test_offset_calculation_for_empty_file(harness):
    check_offsets('', [0])

def test_offset_calculation_advanced(harness):
    raw = (
        '\n\n\n[---]\n'
        'cheese\n[---]\n'
        '\n\n\n\n\n\n[---]\n'
        'Monkey\nHead\n') #Be careful: this is implicit concation, not a tuple
    check_offsets(raw, [0, 4, 6, 13])

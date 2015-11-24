from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from aspen.pagination import split
from pytest import raises


# Tests
# =====

def test_barely_working(harness):
    output = harness.simple('Greetings, program!', 'index.html')
    assert output.media_type == 'text/html'

def test_charset_static_barely_working(harness):
    output = harness.simple( 'Greetings, program!'
                             , 'index.html'
                             , website_configuration={'charset_static': 'OOG'}
                              )
    assert output.media_type == 'text/html'
    assert output.charset == 'OOG'

def test_charset_dynamic_barely_working(harness):
    output = harness.simple( '[---]\n[---]\nGreetings, program!'
                             , 'index.html.spt'
                             , website_configuration={'charset_dynamic': 'CHEESECODE'}
                              )
    assert output.media_type == 'text/html'
    assert output.charset == 'CHEESECODE'

def test_resource_pages_work(harness):
    actual = harness.simple("[---]\nfoo = 'bar'\n[--------]\nGreetings, %(foo)s!").body
    assert actual == "Greetings, bar!"

def test_resource_dunder_all_limits_vars(harness):
    actual = raises( KeyError
                            , harness.simple
                            , "[---]\nfoo = 'bar'\n"
                              "__all__ = []\n"
                              "[---------]\n"
                              "Greetings, %(foo)s!"
                             ).value
    # in production, KeyError is turned into a 500 by an outer wrapper
    assert type(actual) == KeyError

def test_path_part_params_are_available(harness):
    output = harness.simple("""
        [---]
        if 'b' in path.parts[0].params:
            a = path.parts[0].params['a']
        [---]
        %(a)s
    """, '/foo/index.html.spt', '/foo;a=1;b;a=3/')
    assert output.body == "3\n"

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

def test_website_is_in_context(harness):
    output = harness.simple("""
        assert website.__class__.__name__ == 'Website', website
        [--------]
        [--------]
        It worked.""")
    assert output.body == 'It worked.'

def test_unknown_mimetype_yields_default_mimetype(harness):
    output = harness.simple( 'Greetings, program!'
                             , filepath='foo.flugbaggity'
                              )
    assert output.media_type == 'text/plain'

def test_templating_without_script_works(harness):
    output = harness.simple('[-----]\n[-----] via stdlib_format\n{path.raw}')
    assert output.body == '/'


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

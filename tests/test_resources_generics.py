from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.simplates import pagination

#SPLIT TESTS
############

def check_page_content(raw, comp_pages):
    '''
    Pattern function. Splits a raw, then checks the number of pages generated,
    and that each page's content matches the contents of comp_pages.
    Interpretation of comp_pages is as follows:
    comp_pages is am item or a list of items. Each item is a string, tuple, or
    None. If it is a string, the page's content is matched; if it is a tuple,
    the page's content and/or header are checked. If any of the items are None,
    that comparison is ignored.
    '''

    #Convert to single-element list
    if not isinstance(comp_pages, list):
        comp_pages = [comp_pages]

    #Convert all non-tuples to tuples
    comp_pages = [item if isinstance(item, tuple) else (item, None)
                  for item in comp_pages]

    #execute resources.split
    pages = list(pagination.split(raw))

    assert len(pages) == len(comp_pages)

    for generated_page, (content, header) in zip(pages, comp_pages):
        if content is not None:
            assert generated_page.content == content, repr(generated_page.content) + " should be " + repr(content)
        if header is not None:
            assert generated_page.header == header, repr(generated_page.header) + " should be " + repr(header)

def test_empty_content():
    check_page_content('', '')

def test_no_page_breaks():
    content = 'this is some content\nwith newlines'
    check_page_content(content, content)

def test_only_page_break():
    check_page_content('[---]\n', ['', ''])

def test_basic_page_break():
    check_page_content('Page 1\n[---]\nPage 2\n',
                       ['Page 1\n', 'Page 2\n'])

def test_two_page_breaks():
    raw = '''\
1
[---]
2
[---]
3
'''
    check_page_content(raw, ['1\n', '2\n', '3\n'])

def test_no_inline_page_break():
    content = 'this is an[---]inline page break'
    check_page_content(content,  [None])

def test_headers():
    raw = '''\
page1
[---] header2
page2
[---] header3
page3
'''
    pages = [
        ('page1\n', ''),
        ('page2\n', 'header2'),
        ('page3\n', 'header3')]

    check_page_content(raw, pages)
#ESCAPE TESTS
#############

def check_escape(content_to_escape, expected):
    actual = pagination.escape(content_to_escape)
    assert actual == expected, repr(actual) + " should be " + repr(expected)

def test_basic_escape_1():
    check_escape('\[---]', '[---]')

def test_basic_escape_2():
    check_escape('\\\\\\[---]', '\\\[---]')

def test_inline_sep_ignored_1():
    check_escape('inline[---]break', 'inline[---]break')

def test_inline_sep_ignored_2():
    check_escape('inline\\\[---]break', 'inline\\\[---]break')

def test_escape_preserves_extra_content():
    check_escape('\\\\[---] content ', '\[---] content ')

def test_multiple_escapes():
    to_escape = '1\n\[---]\n2\n\[---]'
    result = '1\n[---]\n2\n[---]'
    check_escape(to_escape, result)

def test_long_break():
    check_escape('\[----------]', '[----------]')

def test_escaped_pages():
    raw = '''\
1
[---]
2
\[---]
3
'''
    check_page_content(raw, ['1\n', '2\n\\[---]\n3\n'])

#SPECLINE TESTS
###############

def check_specline(header, media_type, renderer):
    assert pagination.parse_specline(header) == (media_type, renderer)

def test_empty_header_1():
    check_specline('', '', '')

def test_empty_header_2():
    check_specline('    ', '', '')

def test_media_only():
    check_specline('text/plain', 'text/plain', '')

def test_renderer_only():
    check_specline('via renderer', '', 'renderer')

def test_basic_specline():
    check_specline('media/type via renderer', 'media/type', 'renderer')

def test_funky_whitespace():
    check_specline( '  media/type    via   renderer  '
                  , 'media/type'
                  , 'renderer'
                   )

def test_whitespace_in_fields():
    check_specline( 'media type via content renderer'
                  , 'media type'
                  , 'content renderer'
                   )

def test_extra_funky_whitespace():
    header = '   this is a  type   via some sort   of renderer    '
    media_type = 'this is a  type'
    renderer = 'some sort   of renderer'
    check_specline(header, media_type, renderer)

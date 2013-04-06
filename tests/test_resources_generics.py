from aspen import resources

#SPLIT TESTS
############

def check_page_content(raw, comp_pages):
    '''
    Pattern function. Splits a raw, then checks the number of pages generated,
    and that each page's content matches the contents of comp_pages.
    Interpretation of comp_pages is as follows:
    comp_pages is am item or a list of items. Each item is a string or tuple.
    If it is a string, the page's content is matched; if it is a tuple, the
    page's content and/or header are checked.
    '''
    
    #Convert to single-element list
    if not isinstance(comp_pages, list):
        comp_pages = [comp_pages]
        
    #Convert all non-tuples to tuples
    comp_pages = [item if isinstance(item, tuple) else (item, None)
                  for item in comp_pages]
    
    #execute resources.split
    pages = list(resources.split(raw))
    
    assert len(pages) == len(comp_pages)
    
    for generated_page, comp_page in zip(pages, comp_pages):
        content, header = comp_page
        if content is not None:
            assert generated_page.content == content
        if header is not None:
            assert generated_page.header == header
        



def test_empty_content():
    check_page_content('', '')
    
def test_no_page_breaks():
    content = 'this is some content\nwith newlines'
    check_page_content(content, content)
    
def test_only_page_break():
    check_page_content('[----]\n', ['', ''])
    
def test_basic_page_break():
    check_page_content('Page 1\n[----]\nPage 2\n',
                       ['Page 1\n', 'Page 2\n'])
    
def test_two_page_breaks():
    raw = '''1
[----]
2
[----]
3
'''
    check_page_content(raw, ['1\n', '2\n', '3\n'])
    
def test_no_inline_page_break():
    content = 'this is an[----]inline page break'
    check_page_content(content,  [None])
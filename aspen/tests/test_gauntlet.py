import os
from os.path import dirname, join, realpath

from aspen import gauntlet, Response
from aspen.tests import assert_raises, handle
from aspen.tests.fsfix import attach_teardown, mk
from aspen.http.request import Path
from aspen.configuration import Configurable


# Helpers 
# =======

class StubRequest:
    def __init__(self, path):
        self.path = Path(path)
        c = Configurable.from_argv(['fsfix'])
        c.copy_configuration_to(self)

def expect(path):
    """Given a relative path, return an absolute path.

    The incoming path is in UNIX form (/foo/bar.html). The outgoing path is in 
    native form, with symlinks removed.

    """
    path = os.sep.join([dirname(__file__), 'fsfix'] + path.split('/'))
    return realpath(path)


# Indices
# =======

def check_index(path):
    """Given an urlpath, return a filesystem path per gauntlet.virtual_paths.
    """
    request = StubRequest(path)
    parts = gauntlet.translate(request)
    gauntlet.index(request)
    return request

def test_index_is_found():
    mk(('index.html', "Greetings, program!"))
    expected = expect('index.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_alternate_index_is_not_found():
    mk(('default.html', "Greetings, program!"))
    expected = expect('')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_alternate_index_is_found():
    mk( ('.aspen/aspen.conf', '[aspen]\ndefault_filenames = default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = expect('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_overrides_and_doesnt_extend():
    mk( ('.aspen/aspen.conf', '[aspen]\ndefault_filenames = default.html')
      , ('index.html', "Greetings, program!")
       )
    expected = expect('')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_takes_first():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames = index.html default.html')
      , ('index.html', "Greetings, program!")
      , ('default.html', "Greetings, program!")
       )
    expected = expect('index.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_takes_second_if_first_is_missing():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames = index.html default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = expect('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_strips_commas():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames: index.html, default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = expect('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_strips_many_commas():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames: index.html,,,,,,, default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = expect('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_ignores_blanks():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames: index.html,, ,, ,,, default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = expect('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual

def test_index_conf_setting_works_with_only_comma():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames: index.html,default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = expect('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual


# Virtual Paths
# =============

def check_virtual_paths(path):
    """Given an urlpath, return a filesystem path per gauntlet.virtual_paths.
    """
    request = StubRequest(path)
    parts = gauntlet.translate(request)
    gauntlet.virtual_paths(request, parts)
    return request

def test_virtual_path_can_passthrough():
    mk(('foo.html', "Greetings, program!"))
    expected = expect('foo.html')
    actual = check_virtual_paths('foo.html').fs
    assert actual == expected, actual

def test_unfound_virtual_path_passes_through():
    mk(('%bar/foo.html', "Greetings, program!"))
    request = check_virtual_paths('/blah/flah.html')
    expected = expect('/blah/flah.html')
    actual = request.fs
    assert actual == expected, actual

def test_virtual_path_is_virtual():
    mk(('%bar/foo.html', "Greetings, program!"))
    expected = expect('%bar/foo.html')
    actual = check_virtual_paths('/blah/foo.html').fs
    assert actual == expected, actual

def test_virtual_path_sets_request_path():
    mk(('%bar/foo.html', "Greetings, program!"))
    expected = {'bar': 'blah'}
    actual = check_virtual_paths('/blah/foo.html').path
    assert actual == expected, actual

def test_virtual_path_typecasts_to_int():
    mk(('%year.int/foo.html', "Greetings, program!"))
    expected = {'year': 1999}
    actual = check_virtual_paths('/1999/foo.html').path
    assert actual == expected, actual

def test_virtual_path_raises_on_bad_typecast():
    mk(('%year.int/foo.html', "Greetings, program!"))
    assert_raises(Response, check_virtual_paths, '/I am not a year./foo.html')

def test_virtual_path_raises_404_on_bad_typecast():
    mk(('%year.int/foo.html', "Greetings, program!"))
    response = assert_raises(Response, check_virtual_paths, '/I am not a year./foo.html')
    expected = 404
    actual = response.code
    assert actual == expected, actual

def test_virtual_path_raises_on_direct_access():
    mk()
    assert_raises(Response, check_virtual_paths, '/%name/foo.html')

def test_virtual_path_raises_404_on_direct_access():
    mk()
    response = assert_raises(Response, check_virtual_paths, '/%name/foo.html')
    expected = 404
    actual = response.code
    assert actual == expected, actual

def test_virtual_path_matches_the_first():
    mk( ('%first/foo.html', "Greetings, program!")
      , ('%second/foo.html', "WWAAAAAAAAAAAA!!!!!!!!")
       )
    expected = expect('%first/foo.html')
    actual = check_virtual_paths('/1999/foo.html').fs
    assert actual == expected, actual

def test_virtual_path_directory():
    mk(('%first/index.html', "Greetings, program!"))
    expected = expect('%first')
    actual = check_virtual_paths('/foo/').fs
    assert actual == expected, actual

def test_virtual_path_file():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = expect('foo/%bar.html')
    actual = check_virtual_paths('/foo/blah.html').fs
    assert actual == expected, actual

def test_virtual_path_file_only_last_part():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = expect('foo/blah.html/baz')
    actual = check_virtual_paths('/foo/blah.html/baz').fs
    assert actual == expected, actual

def test_virtual_path_file_only_last_part____no_really():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = expect('foo/blah.html/')
    actual = check_virtual_paths('/foo/blah.html/').fs
    assert actual == expected, actual

def test_virtual_path_file_key_val_set():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = {'bar': u'blah'}
    actual = check_virtual_paths('/foo/blah.html').path
    assert actual == expected, actual

def test_virtual_path_file_key_val_not_cast():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = {'bar': u'537'}
    actual = check_virtual_paths('/foo/537.html').path
    assert actual == expected, actual

def test_virtual_path_file_key_val_cast():
    mk(('foo/%bar.int.html', "Greetings, program!"))
    expected = {'bar': 537}
    actual = check_virtual_paths('/foo/537.html').path
    assert actual == expected, actual


# Docs
# ====

def test_virtual_path_docs_1():
    mk(('%name/index.html', "Greetings, {{ request.path['name'] }}!"))
    response = handle('/aspen/')
    expected = "Greetings, aspen!"
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_2():
    mk(('%name/index.html', "Greetings, {{ request.path['name'] }}!"))
    response = handle('/python/')
    expected = "Greetings, python!"
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_3():
    mk( ('%name/index.html', "Greetings, {{ request.path['name'] }}!")
      , ('%name/%cheese.txt', "{{ request.path['name'].title() }} likes {{ request.path['cheese'] }} cheese.")
       )
    response = handle('/chad/cheddar.txt')
    expected = "Chad likes cheddar cheese."
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_4():
    mk( ('%name/index.html', "Greetings, {{ request.path['name'] }}!")
      , ('%name/%cheese.txt', "{{ request.path['name'].title() }} likes {{ request.path['cheese'] }} cheese.")
       )
    response = handle('/chad/cheddar.txt/')
    expected = 404 
    actual = response.code
    assert actual == expected, actual

def test_virtual_path_docs_5():
    mk( ('%name/index.html', "Greetings, {{ request.path['name'] }}!")
      , ('%name/%cheese.txt', "{{ request.path['name'].title() }} likes {{ request.path['cheese'] }} cheese.")
      , ( '%year.int/index.html'
        , "Tonight we're going to party like it's {{ request.path['year'] }}!"
         )
       )
    response = handle('/1999/')
    expected = "Greetings, 1999!"
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_6():
    mk( ( '%year.int/index.html'
        , "Tonight we're going to party like it's {{ request.path['year'] }}!"
         )
       )
    response = handle('/1999/')
    expected = "Tonight we're going to party like it's 1999!"
    actual = response.body
    assert actual == expected, actual


attach_teardown(globals())

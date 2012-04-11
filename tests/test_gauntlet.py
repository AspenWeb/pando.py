import os
from os.path import dirname, join, realpath

from aspen import gauntlet, Response
from aspen.http.request import Request
from aspen.testing import assert_raises, handle, NoException, StubRequest 
from aspen.testing import attach_teardown, fix, FSFIX, mk
from aspen.configuration import Configurable
from aspen.http.mapping import Mapping


# Indices
# =======

def check_index(path):
    """Given an urlpath, return a filesystem path per gauntlet.index.
    """
    request = StubRequest.from_fs(path)
    gauntlet.run_through(request, gauntlet.index)
    return request

def test_index_is_found():
    mk(('index.html', "Greetings, program!"))
    expected = fix('index.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_alternate_index_is_not_found():
    mk(('default.html', "Greetings, program!"))
    expected = fix('')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_alternate_index_is_found():
    mk( ('.aspen/aspen.conf', '[aspen]\ndefault_filenames = default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_overrides_and_doesnt_extend():
    mk( ('.aspen/aspen.conf', '[aspen]\ndefault_filenames = default.html')
      , ('index.html', "Greetings, program!")
       )
    expected = fix('')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_takes_first():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames = index.html default.html')
      , ('index.html', "Greetings, program!")
      , ('default.html', "Greetings, program!")
       )
    expected = fix('index.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_takes_second_if_first_is_missing():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames = index.html default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_strips_commas():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames: index.html, default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_strips_many_commas():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames: index.html,,,,,,, default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_index_conf_setting_ignores_blanks():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames: index.html,, ,, ,,, default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual

def test_index_conf_setting_works_with_only_comma():
    mk( ( '.aspen/aspen.conf'
        , '[aspen]\ndefault_filenames: index.html,default.html')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual


# Virtual Paths
# =============

def check_virtual_paths(path):
    """Given an urlpath, return a filesystem path per gauntlet.virtual_paths.
    """
    request = StubRequest.from_fs(path)
    gauntlet.run_through(request, gauntlet.virtual_paths)
    return request

def test_virtual_path_can_passthrough():
    mk(('foo.html', "Greetings, program!"))
    expected = fix('foo.html')
    actual = check_virtual_paths('foo.html').fs
    assert actual == expected, actual

def test_unfound_virtual_path_passes_through():
    mk(('%bar/foo.html', "Greetings, program!"))
    request = check_virtual_paths('/blah/flah.html')
    expected = fix('/blah/flah.html')
    actual = request.fs
    assert actual == expected, actual

def test_virtual_path_is_virtual():
    mk(('%bar/foo.html', "Greetings, program!"))
    expected = fix('%bar/foo.html')
    actual = check_virtual_paths('/blah/foo.html').fs
    assert actual == expected, actual

def test_virtual_path_sets_request_path():
    mk(('%bar/foo.html', "Greetings, program!"))
    expected = {'bar': [u'blah']}
    actual = check_virtual_paths('/blah/foo.html').line.url.path
    assert actual == expected, actual

def test_virtual_path_typecasts_to_int():
    mk(('%year.int/foo.html', "Greetings, program!"))
    expected = {'year': [1999]}
    actual = check_virtual_paths('/1999/foo.html').line.url.path
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
    expected = fix('%first/foo.html')
    actual = check_virtual_paths('/1999/foo.html').fs
    assert actual == expected, actual

def test_virtual_path_directory():
    mk(('%first/index.html', "Greetings, program!"))
    expected = fix('%first')
    actual = check_virtual_paths('/foo/').fs
    assert actual == expected, actual

def test_virtual_path_file():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = fix('foo/%bar.html')
    actual = check_virtual_paths('/foo/blah.html').fs
    assert actual == expected, actual

def test_virtual_path_file_only_last_part():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = fix('foo/blah.html/baz')
    actual = check_virtual_paths('/foo/blah.html/baz').fs
    assert actual == expected, actual

def test_virtual_path_file_only_last_part____no_really():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = fix('foo/blah.html/')
    actual = check_virtual_paths('/foo/blah.html/').fs
    assert actual == expected, actual

def test_virtual_path_file_key_val_set():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = {'bar': [u'blah']}
    actual = check_virtual_paths('/foo/blah.html').line.url.path
    assert actual == expected, actual

def test_virtual_path_file_key_val_not_cast():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = {'bar': [u'537']}
    actual = check_virtual_paths('/foo/537.html').line.url.path
    assert actual == expected, actual

def test_virtual_path_file_key_val_cast():
    mk(('foo/%bar.int.html', "Greetings, program!"))
    expected = {'bar': [537]}
    actual = check_virtual_paths('/foo/537.html').line.url.path
    assert actual == expected, actual


# trailing slash
# ==============

def check_trailing_slash(path):
    """Given an urlpath, return a filesystem path per gauntlet.trailing_slash.
    """
    request = StubRequest.from_fs(path)
    gauntlet.run_through(request, gauntlet.trailing_slash)
    return request

def test_trailing_slash_passes_files_through():
    mk(('foo/index.html', "Greetings, program!"))
    expected = fix('/foo/537.html')
    actual = check_trailing_slash('/foo/537.html').fs
    assert actual == expected, actual

def test_trailing_slash_passes_dirs_with_slash_through():
    mk('foo')
    expected = fix('/foo/')
    actual = check_trailing_slash('/foo/').fs
    assert actual == expected, actual

def test_trailing_slash_redirects_trailing_slash():
    mk('foo')
    response = assert_raises(Response, check_trailing_slash, '/foo')

    expected = 301
    actual = response.code
    assert actual == expected, actual

def test_trailing_slash_redirects_trailing_slash_to_the_right_place():
    mk('foo')
    response = assert_raises(Response, check_trailing_slash, '/foo')

    expected = '/foo/'
    actual = response.headers.one('Location')
    assert actual == expected, actual


# Docs
# ====

def test_virtual_path_docs_1():
    mk(('%name/index.html', "^L\nGreetings, {{ path['name'] }}!"))
    response = handle('/aspen/')
    expected = "Greetings, aspen!"
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_2():
    mk(('%name/index.html', "^L\nGreetings, {{ path['name'] }}!"))
    response = handle('/python/')
    expected = "Greetings, python!"
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_3():
    mk( ('%name/index.html', "^L\nGreetings, {{ path['name'] }}!")
      , ('%name/%cheese.txt', "^L\n{{ path['name'].title() }} likes {{ path['cheese'] }} cheese.")
       )
    response = handle('/chad/cheddar.txt')
    expected = "Chad likes cheddar cheese."
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_4():
    mk( ('%name/index.html', "^L\nGreetings, {{ path['name'] }}!")
      , ('%name/%cheese.txt', "{{ path['name'].title() }} likes {{ path['cheese'] }} cheese.")
       )
    response = handle('/chad/cheddar.txt/')
    expected = 404 
    actual = response.code
    assert actual == expected, actual

def test_virtual_path_docs_5():
    mk( ('%name/index.html', "^L\nGreetings, {{ path['name'] }}!")
      , ('%name/%cheese.txt', "{{ path['name'].title() }} likes {{ path['cheese'] }} cheese.")
      , ( '%year.int/index.html'
        , "^L\nTonight we're going to party like it's {{ path['year'] }}!"
         )
       )
    response = handle('/1999/')
    expected = "Greetings, 1999!"
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_6():
    mk( ( '%year.int/index.html'
        , "^L\nTonight we're going to party like it's {{ path['year'] }}!"
         )
       )
    response = handle('/1999/')
    expected = "Tonight we're going to party like it's 1999!"
    actual = response.body
    assert actual == expected, actual


# intercept_socket
# ================

def test_intercept_socket_protects_direct_access():
    request = Request(url="/foo.sock")
    assert_raises(Response, gauntlet.intercept_socket, request)

def test_intercept_socket_intercepts_handshake():
    request = Request(url="/foo.sock/1")
    gauntlet.intercept_socket(request)
    
    expected = ('/foo.sock', '1')
    actual = (request.line.url.path.raw, request.socket)
    assert actual == expected, actual

def test_intercept_socket_intercepts_transported():
    request = Request(url="/foo.sock/1/websocket/46327hfjew3?foo=bar")
    gauntlet.intercept_socket(request)

    expected = ('/foo.sock', '1/websocket/46327hfjew3')
    actual = (request.line.url.path.raw, request.socket)
    assert actual == expected, actual


# mongs
# =====
# These surfaced when porting mongs from Aspen 0.8.

def test_virtual_path_parts_can_be_empty():
    return
    mk(('foo/%bar/index.html', "Greetings, program!"))
    expected = {'bar': ''}
    actual = check_virtual_paths('/foo//').line.url.path
    assert actual == expected, actual

def test_file_matches_in_face_of_dir():
    mk( ('%page/index.html', 'Nothing to see here.')
      , ('%value.txt', "Greetings, program!")
       )
    expected = {'value': 'baz'}
    actual = check_virtual_paths('/baz.txt').line.url.path
    assert actual == expected, actual

def test_file_matches_extension():
    mk( ('%value.json', '{"Greetings,": "program!"}')
      , ('%value.txt', "Greetings, program!")
       )
    expected = "%value.json"
    actual = os.path.basename(check_virtual_paths('/baz.json').fs)
    assert actual == expected, actual

def test_file_matches_other_extension():
    mk( ('%value.json', '{"Greetings,": "program!"}')
      , ('%value.txt', "Greetings, program!")
       )
    expected = "%value.txt"
    actual = os.path.basename(check_virtual_paths('/baz.txt').fs)
    assert actual == expected, actual

def test_virtual_file_with_no_extension_works():
    mk(('%value', '{"Greetings,": "program!"}'))
    check_virtual_paths('/baz.txt')
    assert NoException 

def test_normal_file_with_no_extension_works():
    mk( ('%value', '{"Greetings,": "program!"}')
      , ('value', '{"Greetings,": "program!"}')
       )
    check_virtual_paths('/baz.txt')
    assert NoException 

def test_file_with_no_extension_matches():
    mk( ('%value', '{"Greetings,": "program!"}')
      , ('value', '{"Greetings,": "program!"}')
       )
    expected = {'value': 'baz'}
    actual = check_virtual_paths('/baz').line.url.path
    assert actual == expected, actual

attach_teardown(globals())

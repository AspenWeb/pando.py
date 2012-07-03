import os

from aspen import gauntlet, Response
from aspen.http.request import Request
from aspen.testing import assert_raises, handle, NoException, StubRequest 
from aspen.testing import attach_teardown, fix, mk


# Indices
# =======

def check_index(path, *a):
    """Given a uripath, return a filesystem path per gauntlet.index.
    """
    request = StubRequest.from_fs(path, *a)
    gauntlet.run_through(request, gauntlet.index)
    return request

def test_index_is_found():
    mk(('index.html', "Greetings, program!"))
    expected = fix('index.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_negotiated_index_is_found():
    mk(( 'index'
       , """\
^L text/html
<h1>Greetings, program!</h1>
^L text/plain
Greetings, program!
"""))
    expected = fix('index')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_alternate_index_is_not_found():
    mk(('default.html', "Greetings, program!"))
    expected = fix('')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_alternate_index_is_found():
    mk( ('.aspen/configure-aspen.py', 'website.indices += ["default.html"]')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_configure_aspen_py_setting_override_works_too():
    mk( ('.aspen/configure-aspen.py', 'website.indices = ["default.html"]')
      , ('index.html', "Greetings, program!")
       )
    expected = fix('')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_configure_aspen_py_setting_takes_first():
    mk( ( '.aspen/configure-aspen.py'
        , 'website.indices = ["index.html", "default.html"]')
      , ('index.html', "Greetings, program!")
      , ('default.html', "Greetings, program!")
       )
    expected = fix('index.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_configure_aspen_py_setting_takes_second_if_first_is_missing():
    mk( ( '.aspen/configure-aspen.py'
        , 'website.indices = ["index.html", "default.html"]')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_configure_aspen_py_setting_strips_commas():
    mk( ( '.aspen/configure-aspen.py'
        , 'website.indices = ["index.html", "default.html"]')
      , ('default.html', "Greetings, program!")
       )
    expected = fix('default.html')
    actual = check_index('/').fs
    assert actual == expected, actual
    
def test_configure_aspen_py_setting_strips_many_commas():
    mk(('default.html', "Greetings, program!"))
    expected = fix('default.html')
    actual = check_index('/', '--indices', 'index.html,,default.html').fs
    assert actual == expected, actual
    
def test_configure_aspen_py_setting_ignores_blanks():
    mk(('default.html', "Greetings, program!"))
    expected = fix('default.html')
    actual = check_index('/', '--indices', 'index.html, ,default.html').fs
    assert actual == expected, actual

def test_configure_aspen_py_setting_works_with_only_comma():
    mk(('default.html', "Greetings, program!"))
    expected = fix('default.html')
    actual = check_index('/', '--indices', 'index.html, ,default.html').fs
    assert actual == expected, actual


# Negotiated Fall-through 
# =======================

def check_indirect_negotiation(path):
    """Given an urlpath, return a filesystem path per gauntlet.indirect_negotiation.
    """
    request = StubRequest.from_fs(path)
    gauntlet.run_through(request, gauntlet.indirect_negotiation)
    return request

def test_indirect_negotiation_can_passthrough_renderered():
    mk(('foo.html', "Greetings, program!"))
    expected = fix('foo.html')
    actual = check_indirect_negotiation('foo.html').fs
    assert actual == expected, actual

def test_indirect_negotiation_can_passthrough_negotiated():
    mk(('foo', "Greetings, program!"))
    expected = fix('foo')
    actual = check_indirect_negotiation('foo').fs
    assert actual == expected, actual

def test_indirect_negotiation_modifies_one_dot():
    mk(('foo', "Greetings, program!"))
    expected = fix('foo')
    actual = check_indirect_negotiation('foo.html').fs
    assert actual == expected, actual

def test_indirect_negotiation_skips_two_dots():
    mk(('foo.bar', "Greetings, program!"))
    expected = fix('foo.bar.html')
    actual = check_indirect_negotiation('foo.bar.html').fs
    assert actual == expected, actual

def test_indirect_negotiation_prefers_rendered():
    mk( ('foo.html', "Greetings, program!")
      , ('foo', "blah blah blah")
       )
    expected = fix('foo.html')
    actual = check_indirect_negotiation('foo.html').fs
    assert actual == expected, actual

def test_indirect_negotiation_really_prefers_rendered():
    mk( ('foo.html', "Greetings, program!")
      , ('foo.', "blah blah blah")
       )
    expected = fix('foo.html')
    actual = check_indirect_negotiation('foo.html').fs
    assert actual == expected, actual

def test_indirect_negotation_doesnt_do_dirs():
    mk(('foo/bar.html', "Greetings, program!"))
    actual = check_indirect_negotiation('foo.html').fs
    expected = fix('foo.html')
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
    actual = check_virtual_paths('/blah/foo.html').line.uri.path
    assert actual == expected, actual

def test_virtual_path_typecasts_to_int():
    mk(('%year.int/foo.html', "Greetings, program!"))
    expected = {'year': [1999]}
    actual = check_virtual_paths('/1999/foo.html').line.uri.path
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
    actual = check_virtual_paths('/foo/blah.html').line.uri.path
    assert actual == expected, actual

def test_virtual_path_file_key_val_not_cast():
    mk(('foo/%bar.html', "Greetings, program!"))
    expected = {'bar': [u'537']}
    actual = check_virtual_paths('/foo/537.html').line.uri.path
    assert actual == expected, actual

def test_virtual_path_file_key_val_cast():
    mk(('foo/%bar.int.html', "Greetings, program!"))
    expected = {'bar': [537]}
    actual = check_virtual_paths('/foo/537.html').line.uri.path
    assert actual == expected, actual

def test_virtual_path_file_not_dir():
    mk( ('%foo/bar.html', "Greetings from bar!")
      , ('%baz.html', "Greetings from baz!")
       )
    actual = check_virtual_paths('/bal.html').fs
    expected = fix('%baz.html')
    assert actual == expected, actual


# negotiated *and* virtual paths
# ==============================

def test_virtual_path__and_indirect_neg_file_not_dir():
    mk( ('%foo/bar.html', "Greetings from bar!")
      , ('%baz', "Greetings from baz!")
       )
    actual = check_virtual_paths('/bal.html').fs
    expected = fix('%baz')
    assert actual == expected, actual

def test_virtual_path_and_indirect_neg_noext():
    mk( ('%foo/bar', "Greetings program!"))
    actual = check_virtual_paths('/greet/bar').fs
    expected = fix('%foo/bar')
    assert actual == expected, actual

def test_virtual_path_and_indirect_neg_ext():
    mk( ('%foo/bar', "Greetings program!"))
    actual = check_virtual_paths('/greet/bar.html').fs
    expected = fix('%foo/bar')
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
    actual = response.headers['Location']
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
    request = Request(uri="/foo.sock")
    assert_raises(Response, gauntlet.intercept_socket, request)

def test_intercept_socket_intercepts_handshake():
    request = Request(uri="/foo.sock/1")
    gauntlet.intercept_socket(request)
    
    expected = ('/foo.sock', '1')
    actual = (request.line.uri.path.decoded, request.socket)
    assert actual == expected, actual

def test_intercept_socket_intercepts_transported():
    request = Request(uri="/foo.sock/1/websocket/46327hfjew3?foo=bar")
    gauntlet.intercept_socket(request)

    expected = ('/foo.sock', '1/websocket/46327hfjew3')
    actual = (request.line.uri.path.decoded, request.socket)
    assert actual == expected, actual


# mongs
# =====
# These surfaced when porting mongs from Aspen 0.8.

def test_virtual_path_parts_can_be_empty():
    return
    mk(('foo/%bar/index.html', "Greetings, program!"))
    expected = {'bar': ''}
    actual = check_virtual_paths('/foo//').line.uri.path
    assert actual == expected, actual

def test_file_matches_in_face_of_dir():
    mk( ('%page/index.html', 'Nothing to see here.')
      , ('%value.txt', "Greetings, program!")
       )
    expected = {'value': [u'baz']}
    actual = check_virtual_paths('/baz.txt').line.uri.path
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
    expected = {'value': [u'baz']}
    actual = check_virtual_paths('/baz').line.uri.path
    assert actual == expected, actual


def test_aspen_favicon_doesnt_get_clobbered_by_virtual_path():
    mk('%value')
    request = StubRequest.from_fs('/favicon.ico')
    gauntlet.run_through(request, gauntlet.not_found)
    expected = {}
    actual = request.line.uri.path
    assert actual == expected, actual

def test_robots_txt_also_shouldnt_be_redirected():
    mk('%value')
    request = StubRequest.from_fs('/robots.txt')
    err = assert_raises(Response, gauntlet.run_through, request, gauntlet.not_found)
    actual = err.code
    assert actual == 404, actual 

attach_teardown(globals())

import os

from aspen import dispatcher, Response
from aspen.http.request import Request
from aspen.testing import assert_raises, handle, NoException, StubRequest
from aspen.testing import attach_teardown, fix, mk

# Convenience wrappers
def assert_raises_404(func, *args):
    response = assert_raises(Response, func, *args)
    assert response.code == 404, "Got " + str(response.code) + " instead of 404"
    return response

def assert_raises_302(func, *args):
    response = assert_raises(Response, func, *args)
    assert response.code == 302, "Got " + str(response.code) + " instead of 302"
    return response


# Indices
# =======

def check_index(path, *a):
    """Given a uripath, return a filesystem path per dispatcher
    """
    request = StubRequest.from_fs(path, *a)
    dispatcher.dispatch(request)
    return request

def test_index_is_found():
    mk(('index.html', "Greetings, program!"))
    expected = fix('index.html')
    actual = check_index('/').fs
    assert actual == expected, actual

def test_negotiated_index_is_found():
    mk(( 'index'
       , """
[----------] text/html
<h1>Greetings, program!</h1>
[----------] text/plain
Greetings, program!
"""))
    expected = fix('index')
    actual = check_index('/').fs
    assert actual == expected, actual

def test_alternate_index_is_not_found():
    mk(('default.html', "Greetings, program!"))
    assert_raises_404(check_index, '/')

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
    assert_raises_404(check_index, '/')

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

def test_redirect_indices_to_slash():
    mk( ( '.aspen/configure-aspen.py'
        , 'website.indices = ["index.html", "default.html"]')
      , ('index.html', "Greetings, program!")
       )
    assert_raises_302(check_index, '/index.html')

def test_redirect_second_index_to_slash():
    mk( ( '.aspen/configure-aspen.py'
        , 'website.indices = ["index.html", "default.html"]')
      , ('default.html', "Greetings, program!")
       )
    assert_raises_302(check_index, '/default.html')

def test_dont_redirect_second_index_if_first():
    mk( ( '.aspen/configure-aspen.py'
        , 'website.indices = ["index.html", "default.html"]')
      , ('default.html', "Greetings, program!")
      , ('index.html', "Greetings, program!")
       )
    # first index redirects
    assert_raises_302(check_index, '/index.html')
    # second shouldn't
    expected = fix('default.html')
    actual = check_index('/default.html').fs
    assert actual == expected, actual
 


# Negotiated Fall-through
# =======================

def check_indirect_negotiation(path):
    """Given an urlpath, return a filesystem path per dispatcher.dispatch
    """
    request = StubRequest.from_fs(path)
    dispatcher.dispatch(request)
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
    expected = fix('foo.bar')
    actual = check_indirect_negotiation('foo.bar.html').fs
    assert actual == expected, actual + " isn't " + expected

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

def test_indirect_negotiation_really_prefers_rendered_2():
    mk( ('foo.html', "Greetings, program!")
      , ('foo', "blah blah blah")
       )
    expected = fix('foo.html')
    actual = check_indirect_negotiation('foo.html').fs
    assert actual == expected, actual

def test_indirect_negotation_doesnt_do_dirs():
    mk(('foo/bar.html', "Greetings, program!"))
    response = assert_raises_404(check_indirect_negotiation, 'foo.html')


# Virtual Paths
# =============

def check_virtual_paths(path):
    """Given an urlpath, return a filesystem path per dispatcher.dispatch
    """
    request = StubRequest.from_fs(path)
    dispatcher.dispatch(request)
    return request

def test_virtual_path_can_passthrough():
    mk(('foo.html', "Greetings, program!"))
    expected = fix('foo.html')
    actual = check_virtual_paths('foo.html').fs
    assert actual == expected, actual

def test_unfound_virtual_path_passes_through():
    mk(('%bar/foo.html', "Greetings, program!"))
    assert_raises_404(check_virtual_paths, '/blah/flah.html')

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

def test_virtual_path_sets_unicode_request_path():
    mk(('%bar/foo.html', "Greetings, program!"))
    expected = {'bar': [u'\u2603']}
    actual = check_virtual_paths('/%E2%98%83/foo.html').line.uri.path
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
    response = assert_raises_404(check_virtual_paths, '/I am not a year./foo.html')

def test_virtual_path_raises_on_direct_access():
    mk()
    assert_raises(Response, check_virtual_paths, '/%name/foo.html')

def test_virtual_path_raises_404_on_direct_access():
    mk()
    response = assert_raises_404(check_virtual_paths, '/%name/foo.html')

def test_virtual_path_matches_the_first():
    mk( ('%first/foo.html', "Greetings, program!")
      , ('%second/foo.html', "WWAAAAAAAAAAAA!!!!!!!!")
       )
    expected = fix('%first/foo.html')
    actual = check_virtual_paths('/1999/foo.html').fs
    assert actual == expected, actual

def test_virtual_path_directory():
    mk(('%first/index.html', "Greetings, program!"))
    expected = fix('%first/index.html')
    actual = check_virtual_paths('/foo/').fs
    assert actual == expected, actual + " != " + expected

def test_virtual_path_file():
    mk(('foo/%bar.html.spt', "Greetings, program!"))
    expected = fix('foo/%bar.html.spt')
    actual = check_virtual_paths('/foo/blah.html').fs
    assert actual == expected, actual

def test_virtual_path_file_only_last_part():
    mk(('foo/%bar.html.spt', "Greetings, program!"))
    expected = fix('foo/%bar.html.spt')
    actual = check_virtual_paths('/foo/blah/baz.html').fs
    assert actual == expected, actual

def test_virtual_path_file_only_last_part____no_really():
    mk(('foo/%bar.html', "Greetings, program!"))
    assert_raises_404(check_virtual_paths, '/foo/blah.html/')

def test_virtual_path_file_key_val_set():
    mk(('foo/%bar.html.spt', "Greetings, program!"))
    expected = {'bar': [u'blah']}
    actual = check_virtual_paths('/foo/blah.html').line.uri.path
    assert actual == expected, actual

def test_virtual_path_file_key_val_not_cast():
    mk(('foo/%bar.html.spt', "Greetings, program!"))
    expected = {'bar': [u'537']}
    actual = check_virtual_paths('/foo/537.html').line.uri.path
    assert actual == expected, actual

def test_virtual_path_file_key_val_cast():
    mk(('foo/%bar.int.html.spt', "Greetings, program!"))
    expected = {'bar': [537]}
    actual = check_virtual_paths('/foo/537.html').line.uri.path
    assert actual == expected, repr(actual) + " isn't " + repr(expected)

def test_virtual_path_file_not_dir():
    mk( ('%foo/bar.html', "Greetings from bar!")
      , ('%baz.html.spt', "Greetings from baz!")
       )
    expected = fix('%baz.html.spt')
    actual = check_virtual_paths('/bal.html').fs
    assert actual == expected, actual


# negotiated *and* virtual paths
# ==============================

def test_virtual_path__and_indirect_neg_file_not_dir():
    mk( ('%foo/bar.html', "Greetings from bar!")
      , ('%baz.spt', "Greetings from baz!")
       )
    expected = fix('%baz.spt')
    actual = check_virtual_paths('/bal.html').fs
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
    request = StubRequest.from_fs(path)
    dispatcher.dispatch(request)
    return request

def test_dispatcher_passes_through_files():
    mk(('foo/index.html', "Greetings, program!"))
    expected = fix('/foo/537.html')
    assert_raises_404(check_trailing_slash, '/foo/537.html')

def test_trailing_slash_passes_dirs_with_slash_through():
    mk(('foo/index.html', "Greetings, program!"))
    expected = fix('/foo/index.html')
    actual = check_trailing_slash('/foo/').fs
    assert actual == expected, actual

def test_dispatcher_passes_through_virtual_dir_with_trailing_slash():
    mk(('%foo/index.html', "Greetings, program!"))
    expected = fix('/%foo/index.html')
    actual = check_trailing_slash('/foo/').fs
    assert actual == expected, actual + " isn't " + expected

def test_dispatcher_redirects_dir_without_trailing_slash():
    mk('foo')
    response = assert_raises(Response, check_trailing_slash, '/foo')
    expected = (302, '/foo/')
    actual = (response.code, response.headers['Location'])
    assert actual == expected, actual

def test_dispatcher_redirects_virtual_dir_without_trailing_slash():
    mk('%foo')
    response = assert_raises(Response, check_trailing_slash, '/foo')
    expected = (302, '/foo/')
    actual = (response.code, response.headers['Location'])
    assert actual == expected, actual

def test_trailing_on_virtual_paths_missing():
    mk('%foo/%bar/%baz')
    response = assert_raises(Response, check_trailing_slash, '/foo/bar/baz')
    expected = '/foo/bar/baz/'
    actual = response.headers['Location']
    assert actual == expected, actual

def test_trailing_on_virtual_paths():
    mk(('%foo/%bar/%baz/index.html', "Greetings program!"))
    expected = fix('/%foo/%bar/%baz/index.html')
    actual = check_trailing_slash('/foo/bar/baz/').fs
    assert actual == expected, actual + " isn't " + expected


# Docs
# ====

GREETINGS_NAME_SPT = "[-----]\nname = path['name']\n[------]\nGreetings, %(name)s!"

def test_virtual_path_docs_1():
    mk(('%name/index.html.spt', GREETINGS_NAME_SPT))
    expected = "Greetings, aspen!"
    #import pdb; pdb.set_trace()
    response = handle('/aspen/')
    actual = response.body
    assert actual == expected, repr(actual) + " from " + repr(response)

def test_virtual_path_docs_2():
    mk(('%name/index.html.spt', GREETINGS_NAME_SPT))
    expected = "Greetings, python!"
    response = handle('/python/')
    actual = response.body
    assert actual == expected, actual

NAME_LIKES_CHEESE_SPT = "name = path['name'].title()\ncheese = path['cheese']\n[---------]\n%(name)s likes %(cheese)s cheese."

def test_virtual_path_docs_3():
    mk( ( '%name/index.html.spt', GREETINGS_NAME_SPT),
        ( '%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
      )
    response = handle('/chad/cheddar.txt')
    expected = "Chad likes cheddar cheese."
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_4():
    mk( ( '%name/index.html.spt', GREETINGS_NAME_SPT),
        ( '%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
       )
    response = handle('/chad/cheddar.txt/')
    expected = 404
    actual = response.code
    assert actual == expected, actual

PARTY_LIKE_YEAR_SPT = "year = path['year']\n[----------]\nTonight we're going to party like it's %(year)s!"

def test_virtual_path_docs_5():
    mk( ( '%name/index.html.spt', GREETINGS_NAME_SPT),
        ( '%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT),
        ( '%year.int/index.html.spt', PARTY_LIKE_YEAR_SPT)
       )
    response = handle('/1999/')
    expected = "Greetings, 1999!"
    actual = response.body
    assert actual == expected, actual

def test_virtual_path_docs_6():
    mk( ( '%year.int/index.html.spt', PARTY_LIKE_YEAR_SPT))
    response = handle('/1999/')
    expected = "Tonight we're going to party like it's 1999!"
    actual = response.body
    assert actual == expected, actual


# intercept_socket
# ================

def test_intercept_socket_protects_direct_access():
    request = Request(uri="/foo.sock")
    assert_raises(Response, dispatcher.dispatch, request)

def test_intercept_socket_intercepts_handshake():
    request = Request(uri="/foo.sock/1")
    actual = dispatcher.extract_socket_info(request.line.uri.path.decoded)
    expected = ('/foo.sock', '1')
    assert actual == expected, actual

def test_intercept_socket_intercepts_transported():
    request = Request(uri="/foo.sock/1/websocket/46327hfjew3?foo=bar")
    actual = dispatcher.extract_socket_info(request.line.uri.path.decoded)
    expected = ('/foo.sock', '1/websocket/46327hfjew3')
    assert actual == expected, actual

# URI pathsegment parameters

def _extract_params(path):
    return dispatcher.extract_rfc2396_params(path.lstrip('/').split('/'))

def test_extract_path_params_with_none():
    request = Request(uri="/foo/bar")
    actual = _extract_params(request.line.uri.path.decoded)
    expected = (['foo', 'bar'], [{}, {}]) 
    assert actual == expected

def test_extract_path_params_simple():
    request = Request(uri="/foo;a=1;b=2;c/bar;a=2;b=1")
    actual = _extract_params(request.line.uri.path.decoded)
    expected = (['foo', 'bar'], [{'a':'1', 'b':'2', 'c':[]}, {'a':'2', 'b':'1'}]) 
    assert actual == expected

def test_extract_path_params_complex():
    request = Request(uri="/foo;a=1;b=2,3;c/bar;a=2,ab;b=1")
    actual = _extract_params(request.line.uri.path.decoded)
    expected = (['foo', 'bar'], [{'a':'1', 'b':['2', '3'], 'c':[]}, {'a':[ '2', 'ab' ], 'b':'1'}]) 
    assert actual == expected




# mongs
# =====
# These surfaced when porting mongs from Aspen 0.8.

def test_virtual_path_parts_can_be_empty():
    mk(('foo/%bar/index.html.spt', "Greetings, program!"))
    expected = {u'bar': [u'']}
    actual = check_virtual_paths('/foo//').line.uri.path
    assert actual == expected, actual

def test_file_matches_in_face_of_dir():
    mk( ('%page/index.html.spt', 'Nothing to see here.')
      , ('%value.txt.spt', "Greetings, program!")
       )
    expected = {'value': [u'baz']}
    actual = check_virtual_paths('/baz.txt').line.uri.path
    assert actual == expected, actual

def test_file_matches_extension():
    mk( ('%value.json.spt', '{"Greetings,": "program!"}')
      , ('%value.txt.spt', "Greetings, program!")
       )
    expected = "%value.json.spt"
    actual = os.path.basename(check_virtual_paths('/baz.json').fs)
    assert actual == expected, actual

def test_file_matches_other_extension():
    mk( ('%value.json.spt', '{"Greetings,": "program!"}')
      , ('%value.txt.spt', "Greetings, program!")
       )
    expected = "%value.txt.spt"
    actual = os.path.basename(check_virtual_paths('/baz.txt').fs)
    assert actual == expected, actual

def test_virtual_file_with_no_extension_works():
    mk(('%value.spt', '{"Greetings,": "program!"}'))
    check_virtual_paths('/baz.txt')
    assert NoException

def test_normal_file_with_no_extension_works():
    mk( ('%value.spt', '{"Greetings,": "program!"}')
      , ('value', '{"Greetings,": "program!"}')
       )
    check_virtual_paths('/baz.txt')
    assert NoException

def test_file_with_no_extension_matches():
    mk( ('%value.spt', '{"Greetings,": "program!"}')
      , ('value', '{"Greetings,": "program!"}')
       )
    expected = {'value': [u'baz']}
    actual = check_virtual_paths('/baz').line.uri.path
    assert actual == expected, actual

def test_aspen_favicon_doesnt_get_clobbered_by_virtual_path():
    mk('%value.spt')
    request = StubRequest.from_fs('/favicon.ico')
    dispatcher.dispatch(request)
    expected = {}
    actual = request.line.uri.path
    assert actual == expected, actual

def test_robots_txt_also_shouldnt_be_redirected():
    mk('%value.spt')
    request = StubRequest.from_fs('/robots.txt')
    err = assert_raises(Response, dispatcher.dispatch, request)
    actual = err.code
    assert actual == 404, actual

attach_teardown(globals())

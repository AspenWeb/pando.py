from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

import pytest
from pytest import raises

from aspen import dispatcher, Response
from aspen.http.request import Request
from aspen.testing import handle, NoException, StubRequest


# Helpers
# =======

def assert_raises_404(func, *args):
    response = raises(Response, func, *args).value
    assert response.code == 404
    return response

def assert_raises_302(func, *args):
    response = raises(Response, func, *args).value
    assert response.code == 302
    return response


@pytest.yield_fixture
def check_(harness):
    def _(url_path, fs_path, www, project=(), want='fs'):
        harness.fs.www.mk(*www)
        harness.fs.project.mk(*project)
        expected = harness.fs.www.resolve(fs_path)
        actual = harness.get(url_path, run_through='dispatch_request_to_filesystem')['request']
        for name in want.split('.'):
            actual = getattr(actual, name)
        return actual, expected
    yield _


# Indices
# =======

def test_index_is_found(check_):
    actual, expected = check_('/', 'index.html', ('index.html', "Greetings, program!"))
    assert actual == expected

def test_negotiated_index_is_found(check_):
    actual, expected = check_('/', 'index', ('index',
"""
[----------] text/html
<h1>Greetings, program!</h1>
[----------] text/plain
Greetings, program!
"""))
    assert actual == expected

def test_alternate_index_is_not_found(check_):
    assert_raises_404(check_, '/', '', ('default.html', "Greetings, program!"))

def test_alternate_index_is_found(check_):
    www = (('default.html', "Greetings, program!"),)
    project = (('configure-aspen.py', 'website.indices += ["default.html"]'),)
    actual, expected = check_('/', 'default.html', www, project)
    assert actual == expected

def test_configure_aspen_py_setting_override_works_too(check_):
    www = ( ('.aspen/configure-aspen.py', 'website.indices = ["default.html"]')
          , ('index.html', "Greetings, program!")
           )
    assert_raises_404(check_, '/', '', www)

def test_configure_aspen_py_setting_takes_first(check_):
    www = ( ( '.aspen/configure-aspen.py'
            , 'website.indices = ["index.html", "default.html"]')
          , ('index.html', "Greetings, program!")
          , ('default.html', "Greetings, program!")
           )
    actual, expected = check_('/', 'index.html', www)
    assert actual == expected

def test_configure_aspen_py_setting_takes_second_if_first_is_missing(check_):
    www = ( ( '.aspen/configure-aspen.py'
            , 'website.indices = ["index.html", "default.html"]')
          , ('default.html', "Greetings, program!")
           )
    actual, expected = check_('/', 'default.html', www)
    assert actual == expected

def test_configure_aspen_py_setting_strips_commas(check_):
    www = ( ( '.aspen/configure-aspen.py'
            , 'website.indices = ["index.html", "default.html"]')
          , ('default.html', "Greetings, program!")
           )
    actual, expected = check_('/', 'default.html', www)
    assert actual == expected

def test_redirect_indices_to_slash(check_):
    www = ( ( '.aspen/configure-aspen.py'
            , 'website.indices = ["index.html", "default.html"]'
             )
          , ('index.html', "Greetings, program!")
           )
    assert_raises_302(check_, '/index.html', '', www)

def test_redirect_second_index_to_slash(check_):
    www = ( ( '.aspen/configure-aspen.py'
            , 'website.indices = ["index.html", "default.html"]')
          , ('default.html', "Greetings, program!")
           )
    assert_raises_302(check_, '/default.html', '', www)

def test_dont_redirect_second_index_if_first(check_):
    www = ( ( '.aspen/configure-aspen.py'
            , 'website.indices = ["index.html", "default.html"]')
          , ('default.html', "Greetings, program!")
          , ('index.html', "Greetings, program!")
           )
    # first index redirects
    assert_raises_302(check_, '/index.html', '', www)
    # second shouldn't
    actual, expected = check_('/default.html', 'default.html', www)
    assert actual == expected


# Negotiated Fall-through
# =======================

def test_indirect_negotiation_can_passthrough_renderered(check_):
    actual, expected = check_('foo.html', 'foo.html', ('foo.html', "Greetings, program!"))
    assert actual == expected

def test_indirect_negotiation_can_passthrough_negotiated(check_):
    actual, expected = check_('foo', 'foo', ('foo', "Greetings, program!"))
    assert actual == expected

def test_indirect_negotiation_modifies_one_dot(check_):
    actual, expected = check_('foo.html', 'foo', ('foo', "Greetings, program!"))
    assert actual == expected

def test_indirect_negotiation_skips_two_dots(check_):
    actual, expected = check_('foo.bar.html', 'foo.bar', ('foo.bar', "Greetings, program!"))
    assert actual == expected

def test_indirect_negotiation_prefers_rendered(check_):
    www = ( ('foo.html', "Greetings, program!")
          , ('foo', "blah blah blah")
           )
    actual, expected = check_('foo.html', 'foo.html', www)
    assert actual == expected

def test_indirect_negotiation_really_prefers_rendered(check_):
    www = ( ('foo.html', "Greetings, program!")
          , ('foo.', "blah blah blah")
           )
    actual, expected = check_('foo.html', 'foo.html', www)
    assert actual == expected

def test_indirect_negotiation_really_prefers_rendered_2(check_):
    www = ( ('foo.html', "Greetings, program!")
          , ('foo', "blah blah blah")
           )
    actual, expected = check_('foo.html', 'foo.html', www)
    assert actual == expected

def test_indirect_negotation_doesnt_do_dirs(check_):
    assert_raises_404(check_, 'foo.html', '', ('foo/bar.html', "Greetings, program!"))


# Virtual Paths
# =============

def test_virtual_path_can_passthrough(check_):
    actual, expected = check_('foo.html', 'foo.html', ('foo.html', "Greetings, program!"))
    assert actual == expected

def test_unfound_virtual_path_passes_through(check_):
    assert_raises_404(check_, '/blah/flah.html', '', ('%bar/foo.html', "Greetings, program!"))

def test_virtual_path_is_virtual(check_):
    actual, expected = check_( '/blah/foo.html'
                             , '%bar/foo.html'
                             , ('%bar/foo.html', "Greetings, program!")
                              )
    assert actual == expected

def test_virtual_path_sets_request_path(check_):
    actual, expected = check_( '/blah/foo.html'
                             , {'bar': [u'blah']}
                             , ('%bar/foo.html', "Greetings, program!")
                             , want='line.uri.path'
                              )
    assert actual == expected

def test_virtual_path_sets_unicode_request_path(check_):
    actual, expected = check_( '/%E2%98%83/foo.html'
                             , {'bar': [u'\u2603']}
                             , ('%bar/foo.html', "Greetings, program!")
                             , want='line.uri.path'
                              )
    assert actual == expected

def test_virtual_path_typecasts_to_int(check_):
    actual, expected = check_( '/1999/foo.html'
                             , {'year': [1999]}
                             , ('%year.int/foo.html', "Greetings, program!")
                             , want='line.uri.path'
                              )
    assert actual == expected

def test_virtual_path_raises_on_bad_typecast(check_):
    www = ('%year.int/foo.html', "Greetings, program!")
    raises(Response, check_, '/I am not a year./foo.html', '', www)

def test_virtual_path_raises_404_on_bad_typecast(check_):
    www = ('%year.int/foo.html', "Greetings, program!")
    assert_raises_404(check_, '/I am not a year./foo.html', '', www)

def test_virtual_path_raises_on_direct_access(check_):
    raises(Response, check_, '/%name/foo.html', '', ())

def test_virtual_path_raises_404_on_direct_access(check_):
    assert_raises_404(check_, '/%name/foo.html', '', ())

def test_virtual_path_matches_the_first(check_):
    www = ( ('%first/foo.html', "Greetings, program!")
          , ('%second/foo.html', "WWAAAAAAAAAAAA!!!!!!!!")
           )
    actual, expected = check_('/1999/foo.html', '%first/foo.html', www)
    assert actual == expected

def test_virtual_path_directory(check_):
    actual, expected = check_( '/foo/'
                             , '%first/index.html'
                             , ('%first/index.html', "Greetings, program!")
                              )
    assert actual == expected

def test_virtual_path_file(check_):
    actual, expected = check_( '/foo/blah.html'
                             , 'foo/%bar.html.spt'
                             , ('foo/%bar.html.spt', "Greetings, program!")
                              )
    assert actual == expected

def test_virtual_path_file_only_last_part(check_):
    actual, expected = check_( '/foo/blah/baz.html'
                             , 'foo/%bar.html.spt'
                             , ('foo/%bar.html.spt', "Greetings, program!")
                              )
    assert actual == expected

def test_virtual_path_file_only_last_part____no_really(check_):
    assert_raises_404(check_, '/foo/blah.html/', ('foo/%bar.html', "Greetings, program!"))

def test_virtual_path_file_key_val_set(check_):
    actual, expected = check_( '/foo/blah.html'
                             , {'bar': [u'blah']}
                             , ('foo/%bar.html.spt', "Greetings, program!")
                             , want='line.uri.path'
                              )
    assert actual == expected

def test_virtual_path_file_key_val_not_cast(check_):
    actual, expected = check_( '/foo/537.html'
                             , {'bar': [u'537']}
                             , ('foo/%bar.html.spt', "Greetings, program!")
                             , want='line.uri.path'
                              )
    assert actual == expected

def test_virtual_path_file_key_val_cast(check_):
    actual, expected = check_( '/foo/537.html'
                             , {'bar': [537]}
                             , ('foo/%bar.int.html.spt', "Greetings, program!")
                             , want='line.uri.path'
                              )
    assert actual == expected

def test_virtual_path_file_not_dir(check_):
    www = ( ('%foo/bar.html', "Greetings from bar!")
          , ('%baz.html.spt', "Greetings from baz!")
           )
    actual, expected = check_('/bal.html', '%baz.html.spt', www)
    assert actual == expected


# negotiated *and* virtual paths
# ==============================

def test_virtual_path__and_indirect_neg_file_not_dir(check_):
    www = ( ('%foo/bar.html', "Greetings from bar!")
          , ('%baz.spt', "Greetings from baz!")
           )
    actual, expected = check_('/bal.html', '%baz.spt', www)
    assert actual == expected

def test_virtual_path_and_indirect_neg_noext(check_):
    www = ('%foo/bar', "Greetings program!")
    actual, expected = check_('/greet/bar', '%foo/bar', www)
    assert actual == expected

def test_virtual_path_and_indirect_neg_ext(check_):
    www = ( ('%foo/bar', "Greetings program!"))
    actual, expected = check_('/greet/bar.html', '%foo/bar', www)
    assert actual == expected


# trailing slash
# ==============

def test_dispatcher_passes_through_files(check_):
    assert_raises_404(check_, '/foo/537.html', ('foo/index.html', "Greetings, program!"))

def test_trailing_slash_passes_dirs_with_slash_through(check_):
    actual, expected = check_( '/foo/'
                             , '/foo/index.html'
                             , ('foo/index.html', "Greetings, program!")
                              )
    assert actual == expected

def test_dispatcher_passes_through_virtual_dir_with_trailing_slash(check_):
    actual, expected = check_( '/foo/'
                             , '/%foo/index.html'
                             , ('%foo/index.html', "Greetings, program!")
                              )
    assert actual == expected

def test_dispatcher_redirects_dir_without_trailing_slash(check_):
    mk('foo')
    response = raises(Response, check_, '/foo').value
    expected = (302, '/foo/')
    actual = (response.code, response.headers['Location'])
    assert actual == expected

def test_dispatcher_redirects_virtual_dir_without_trailing_slash(check_):
    mk('%foo')
    response = raises(Response, check_, '/foo').value
    expected = (302, '/foo/')
    actual = (response.code, response.headers['Location'])
    assert actual == expected

def test_trailing_on_virtual_paths_missing(check_):
    mk('%foo/%bar/%baz')
    response = raises(Response, check_, '/foo/bar/baz').value
    expected = '/foo/bar/baz/'
    actual = response.headers['Location']
    assert actual == expected

def test_trailing_on_virtual_paths(check_):
    actual, expected = check_( '/foo/bar/baz/'
                             , '/%foo/%bar/%baz/index.html'
                             , ('%foo/%bar/%baz/index.html', "Greetings program!")
                              )
    assert actual == expected

def test_dont_confuse_files_for_dirs(check_):
    www = ( ('foo.html', 'Greetings, Program!') )
    response = raises(Response, check_, '/foo.html/bar').value
    assert response.code == 404



# path part params
# ================

def test_path_part_with_params_works(check_):
    actual, expected = check_( '/foo;a=1/'
                             , '/foo/index.html'
                             , ('foo/index.html', "Greetings program!")
                              )
    assert actual == expected

def test_path_part_params_vpath(check_):
    actual, expected = check_( '/foo;a=1;b=;a=2;b=3/'
                             , '/%bar/index.html'
                             , ('%bar/index.html', "Greetings program!")
                              )
    assert actual == expected

def test_path_part_params_static_file(check_):
    actual, expected = check_( '/foo/bar.html;a=1;b=;a=2;b=3'
                             , '/foo/bar.html'
                             , ('/foo/bar.html', "Greetings program!")
                              )
    assert actual == expected

def test_path_part_params_simplate(check_):
    actual, expected = check_( '/foo/bar.html;a=1;b=;a=2;b=3'
                             , '/foo/bar.html.spt'
                             , ('/foo/bar.html.spt', "Greetings program!")
                              )
    assert actual == expected

def test_path_part_params_negotiated_simplate(check_):
    actual, expected = check_( '/foo/bar.html;a=1;b=;a=2;b=3'
                             , '/foo/bar.spt'
                             , ('/foo/bar.spt', "Greetings program!")
                              )
    assert actual == expected

def test_path_part_params_greedy_simplate(check_):
    actual, expected = check_( '/foo/baz/buz;a=1;b=;a=2;b=3/blam.html'
                             , '/foo/%bar.spt'
                             , ('/foo/%bar.spt', "Greetings program!")
                              )
    assert actual == expected


# Docs
# ====

GREETINGS_NAME_SPT = "[-----]\nname = path['name']\n[------]\nGreetings, %(name)s!"

def test_virtual_path_docs_1(check_):
    mk(('%name/index.html.spt', GREETINGS_NAME_SPT))
    expected = "Greetings, aspen!"
    response = handle('/aspen/')
    actual = response.body
    assert actual == expected

def test_virtual_path_docs_2(check_):
    mk(('%name/index.html.spt', GREETINGS_NAME_SPT))
    expected = "Greetings, python!"
    response = handle('/python/')
    actual = response.body
    assert actual == expected

NAME_LIKES_CHEESE_SPT = "name = path['name'].title()\ncheese = path['cheese']\n[---------]\n%(name)s likes %(cheese)s cheese."

def test_virtual_path_docs_3(check_):
    www = ( ( '%name/index.html.spt', GREETINGS_NAME_SPT)
          , ( '%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
           )
    response = handle('/chad/cheddar.txt')
    expected = "Chad likes cheddar cheese."
    actual = response.body
    assert actual == expected

def test_virtual_path_docs_4(check_):
    www = ( ( '%name/index.html.spt', GREETINGS_NAME_SPT)
          , ( '%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
           )
    response = handle('/chad/cheddar.txt/')
    expected = 404
    actual = response.code
    assert actual == expected

PARTY_LIKE_YEAR_SPT = "year = path['year']\n[----------]\nTonight we're going to party like it's %(year)s!"

def test_virtual_path_docs_5(check_):
    www = ( ( '%name/index.html.spt', GREETINGS_NAME_SPT)
          , ( '%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
          , ( '%year.int/index.html.spt', PARTY_LIKE_YEAR_SPT)
           )
    response = handle('/1999/')
    expected = "Greetings, 1999!"
    actual = response.body
    assert actual == expected

def test_virtual_path_docs_6(check_):
    www = (('%year.int/index.html.spt', PARTY_LIKE_YEAR_SPT))
    response = handle('/1999/')
    expected = "Tonight we're going to party like it's 1999!"
    actual = response.body
    assert actual == expected


# intercept_socket
# ================

def test_intercept_socket_protects_direct_access():
    request = Request(uri="/foo.sock")
    raises(Response, dispatcher.dispatch, request)

def test_intercept_socket_intercepts_handshake():
    request = Request(uri="/foo.sock/1")
    actual = dispatcher.extract_socket_info(request.line.uri.path.decoded)
    expected = ('/foo.sock', '1')
    assert actual == expected

def test_intercept_socket_intercepts_transported():
    request = Request(uri="/foo.sock/1/websocket/46327hfjew3?foo=bar")
    actual = dispatcher.extract_socket_info(request.line.uri.path.decoded)
    expected = ('/foo.sock', '1/websocket/46327hfjew3')
    assert actual == expected


# mongs
# =====
# These surfaced when porting mongs from Aspen 0.8.

def test_virtual_path_parts_can_be_empty(check_):
    actual, expected = check_( '/foo//'
                             , {u'bar': [u'']}
                             , ('foo/%bar/index.html.spt', "Greetings, program!")
                             , want='line.uri.path'
                              )
    assert actual == expected

def test_file_matches_in_face_of_dir(check_):
    www = ( ('%page/index.html.spt', 'Nothing to see here.')
          , ('%value.txt.spt', "Greetings, program!")
           )
    {'value': [u'baz']}
    actual, expected = check_('/baz.txt').line.uri.path
    assert actual == expected

def test_file_matches_extension(check_):
    www = ( ('%value.json.spt', '{"Greetings,": "program!"}')
          , ('%value.txt.spt', "Greetings, program!")
           )
    expected = "%value.json.spt"
    actual = os.path.basename(check_('/baz.json').fs)
    assert actual == expected

def test_file_matches_other_extension(check_):
    www = ( ('%value.json.spt', '{"Greetings,": "program!"}')
          , ('%value.txt.spt', "Greetings, program!")
           )
    expected = "%value.txt.spt"
    actual = os.path.basename(check_('/baz.txt').fs)
    assert actual == expected

def test_virtual_file_with_no_extension_works(check_):
    check_('/baz.txt', '', ('%value.spt', '{"Greetings,": "program!"}'))
    assert NoException

def test_normal_file_with_no_extension_works(check_):
    www = ( ('%value.spt', '{"Greetings,": "program!"}')
          , ('value', '{"Greetings,": "program!"}')
           )
    check_('/baz.txt')
    assert NoException

def test_file_with_no_extension_matches(check_):
    www = ( ('%value.spt', '{"Greetings,": "program!"}')
          , ('value', '{"Greetings,": "program!"}')
           )
    {'value': [u'baz']}
    actual, expected = check_('/baz').line.uri.path
    assert actual == expected

def test_aspen_favicon_doesnt_get_clobbered_by_virtual_path(check_):
    mk('%value.spt')
    request = StubRequest.from_fs('/favicon.ico')
    dispatcher.dispatch(request)
    {}
    actual = request.line.uri.path
    assert actual == expected

def test_robots_txt_also_shouldnt_be_redirected(check_):
    mk('%value.spt')
    request = StubRequest.from_fs('/robots.txt')
    err = raises(Response, dispatcher.dispatch, request).value
    actual = err.code
    assert actual == 404

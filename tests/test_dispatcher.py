from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

from aspen import dispatcher, Response
from aspen.http.request import Request
from aspen.testing.filesystem_fixture import FilesystemFixture
from aspen.testing.harness import Harness
from aspen.website import Website


# Helpers
# =======

def assert_raises_404(*args):
    response = raises(Response, check, *args).value
    assert response.code == 404
    return response

def assert_raises_302(*args):
    response = raises(Response, check, *args).value
    assert response.code == 302
    return response


def _handle(url_path, expected, www, project=(), run_through=None, want='response'):
    www = FilesystemFixture(www)
    project = FilesystemFixture(project)
    website = Website(['--www_root', www.root, '--project_root', project.root])
    harness = Harness(website, www, project)

    if want == 'request.fs':
        expected = harness.fs.www.resolve(expected)
    else:
        expected = expected

    thing = harness.get(url_path, run_through=run_through)

    attr_path = want.split('.')
    base = attr_path[0]
    attr_path = attr_path[1:]

    if run_through is None:
        actual = thing
    else:
        actual = thing[base]

    for name in attr_path:
        actual = getattr(actual, name)

    return actual, expected


def _check(*a, **kw):
    kw['run_through'] = 'dispatch_request_to_filesystem'
    if 'want' not in kw:
        kw['want'] = 'request.fs'
    return handle(*a, **kw)


# Indices
# =======

def test_index_is_found(harness):
    expected = harness.fs.www.resolve('index.html')
    actual = harness.make_request('Greetings, program!', 'index.html').fs
    assert actual == expected

def test_negotiated_index_is_found(harness):
    expected = harness.fs.www.resolve('index')
    actual = harness.make_request('''
        [----------] text/html
        <h1>Greetings, program!</h1>
        [----------] text/plain
        Greetings, program!
    ''', 'index').fs
    assert actual == expected

def test_alternate_index_is_not_found():
    assert_raises_404('/', '', (('default.html', "Greetings, program!"),))

def test_alternate_index_is_found():
    www = (('default.html', "Greetings, program!"),)
    project = (('configure-aspen.py', 'website.indices += ["default.html"]'),)
    actual, expected = check('/', 'default.html', www, project)
    assert actual == expected

def test_configure_aspen_py_setting_override_works_too():
    www = (('index.html', "Greetings, program!"),)
    project = (('configure-aspen.py', 'website.indices = ["default.html"]'),)
    assert_raises_404('/', '', www, project)

def test_configure_aspen_py_setting_takes_first():
    project = (('configure-aspen.py', 'website.indices = ["index.html", "default.html"]'),)
    www = ( ('index.html', "Greetings, program!")
          , ('default.html', "Greetings, program!")
           )
    actual, expected = check('/', 'index.html', www, project)
    assert actual == expected

def test_configure_aspen_py_setting_takes_second_if_first_is_missing():
    project = (('configure-aspen.py', 'website.indices = ["index.html", "default.html"]'),)
    www = (('default.html', "Greetings, program!"),)
    actual, expected = check('/', 'default.html', www, project)
    assert actual == expected

def test_configure_aspen_py_setting_strips_commas():
    project = (('configure-aspen.py', 'website.indices = ["index.html", "default.html"]'),)
    www = (('default.html', "Greetings, program!"),)
    actual, expected = check('/', 'default.html', www, project)
    assert actual == expected

def test_redirect_indices_to_slash():
    project = (('configure-aspen.py', 'website.indices = ["index.html", "default.html"]'),)
    www = (('index.html', "Greetings, program!"),)
    assert_raises_302('/index.html', '', www, project)

def test_redirect_second_index_to_slash():
    project = (('configure-aspen.py', 'website.indices = ["index.html", "default.html"]'),)
    www = (('default.html', "Greetings, program!"),)
    assert_raises_302('/default.html', '', www, project)

def test_dont_redirect_second_index_if_first():
    project = (('configure-aspen.py', 'website.indices = ["index.html", "default.html"]'),)
    www = (('default.html', "Greetings, program!"), ('index.html', "Greetings, program!"),)
    # first index redirects
    assert_raises_302('/index.html', '', www, project)
    # second shouldn't
    actual, expected = check('/default.html', 'default.html', www, project)
    assert actual == expected


# Negotiated Fall-through
# =======================

def test_indirect_negotiation_can_passthrough_static():
    actual, expected = check('foo.html', 'foo.html', (('foo.html', "Greetings, program!"),))
    assert actual == expected

def test_indirect_negotiation_can_passthrough_renderered():
    www = (('foo.html.spt', "Greetings, program!"),)
    actual, expected = check('foo.html', 'foo.html.spt', www)
    assert actual == expected

def test_indirect_negotiation_can_passthrough_negotiated():
    actual, expected = check('foo', 'foo', (('foo', "Greetings, program!"),))
    assert actual == expected

def test_indirect_negotiation_modifies_one_dot():
    actual, expected = check('foo.html', 'foo', (('foo', "Greetings, program!"),))
    assert actual == expected

def test_indirect_negotiation_skips_two_dots():
    actual, expected = check('foo.bar.html', 'foo.bar', (('foo.bar', "Greetings, program!"),))
    assert actual == expected

def test_indirect_negotiation_prefers_rendered():
    www = ( ('foo.html', "Greetings, program!")
          , ('foo', "blah blah blah")
           )
    actual, expected = check('foo.html', 'foo.html', www)
    assert actual == expected

def test_indirect_negotiation_really_prefers_rendered():
    www = ( ('foo.html', "Greetings, program!")
          , ('foo.', "blah blah blah")
           )
    actual, expected = check('foo.html', 'foo.html', www)
    assert actual == expected

def test_indirect_negotiation_really_prefers_rendered_2():
    www = ( ('foo.html', "Greetings, program!")
          , ('foo', "blah blah blah")
           )
    actual, expected = check('foo.html', 'foo.html', www)
    assert actual == expected

def test_indirect_negotation_doesnt_do_dirs():
    assert_raises_404('foo.html', '', (('foo/bar.html', "Greetings, program!"),))


# Virtual Paths
# =============

def test_virtual_path_can_passthrough():
    actual, expected = check('foo.html', 'foo.html', (('foo.html', "Greetings, program!"),))
    assert actual == expected

def test_unfound_virtual_path_passes_through():
    assert_raises_404('/blah/flah.html', '', (('%bar/foo.html', "Greetings, program!"),))

def test_virtual_path_is_virtual():
    actual, expected = check( '/blah/foo.html'
                            , '%bar/foo.html'
                            , (('%bar/foo.html', "Greetings, program!"),)
                             )
    assert actual == expected

def test_virtual_path_sets_request_path():
    actual, expected = check( '/blah/foo.html'
                            , {'bar': [u'blah']}
                            , (('%bar/foo.html', "Greetings, program!"),)
                            , want='request.line.uri.path'
                             )
    assert actual == expected

def test_virtual_path_sets_unicode_request_path():
    actual, expected = check( b'/%E2%98%83/foo.html'
                            , {'bar': [u'\u2603']}
                            , (('%bar/foo.html', "Greetings, program!"),)
                            , want='request.line.uri.path'
                             )
    assert actual == expected

def test_virtual_path_typecasts_to_int():
    actual, expected = check( '/1999/foo.html'
                            , {'year': [1999]}
                            , (('%year.int/foo.html', "Greetings, program!"),)
                            , want='request.line.uri.path'
                             )
    assert actual == expected

def test_virtual_path_raises_on_bad_typecast():
    www = (('%year.int/foo.html', "Greetings, program!"),)
    raises(Response, check, '/I am not a year./foo.html', '', www)

def test_virtual_path_raises_404_on_bad_typecast():
    www = (('%year.int/foo.html', "Greetings, program!"),)
    assert_raises_404('/I am not a year./foo.html', '', www)

def test_virtual_path_raises_on_direct_access():
    raises(Response, check, '/%name/foo.html', '', ())

def test_virtual_path_raises_404_on_direct_access():
    assert_raises_404('/%name/foo.html', '', ())

def test_virtual_path_matches_the_first():
    www = ( ('%first/foo.html', "Greetings, program!")
          , ('%second/foo.html', "WWAAAAAAAAAAAA!!!!!!!!")
           )
    actual, expected = check('/1999/foo.html', '%first/foo.html', www)
    assert actual == expected

def test_virtual_path_directory():
    actual, expected = check( '/foo/'
                            , '%first/index.html'
                            , (('%first/index.html', "Greetings, program!"),)
                             )
    assert actual == expected

def test_virtual_path_file():
    actual, expected = check( '/foo/blah.html'
                            , 'foo/%bar.html.spt'
                            , (('foo/%bar.html.spt', "Greetings, program!"),)
                             )
    assert actual == expected

def test_virtual_path_file_only_last_part():
    actual, expected = check( '/foo/blah/baz.html'
                            , 'foo/%bar.html.spt'
                            , (('foo/%bar.html.spt', "Greetings, program!"),)
                             )
    assert actual == expected

def test_virtual_path_file_only_last_part____no_really():
    assert_raises_404('/foo/blah.html/', '', (('foo/%bar.html', "Greetings, program!"),))

def test_virtual_path_file_key_val_set():
    actual, expected = check( '/foo/blah.html'
                            , {'bar': [u'blah']}
                            , (('foo/%bar.html.spt', "Greetings, program!"),)
                            , want='request.line.uri.path'
                             )
    assert actual == expected

def test_virtual_path_file_key_val_not_cast():
    actual, expected = check( '/foo/537.html'
                            , {'bar': [u'537']}
                            , (('foo/%bar.html.spt', "Greetings, program!"),)
                            , want='request.line.uri.path'
                             )
    assert actual == expected

def test_virtual_path_file_key_val_cast():
    actual, expected = check( '/foo/537.html'
                            , {'bar': [537]}
                            , (('foo/%bar.int.html.spt', "Greetings, program!"),)
                            , want='request.line.uri.path'
                             )
    assert actual == expected

def test_virtual_path_file_not_dir():
    www = ( ('%foo/bar.html', "Greetings from bar!")
          , ('%baz.html.spt', "Greetings from baz!")
           )
    actual, expected = check('/bal.html', '%baz.html.spt', www)
    assert actual == expected


# negotiated *and* virtual paths
# ==============================

def test_virtual_path__and_indirect_neg_file_not_dir():
    www = ( ('%foo/bar.html', "Greetings from bar!")
          , ('%baz.spt', "Greetings from baz!")
           )
    actual, expected = check('/bal.html', '%baz.spt', www)
    assert actual == expected

def test_virtual_path_and_indirect_neg_noext():
    www = (('%foo/bar', "Greetings program!"),)
    actual, expected = check('/greet/bar', '%foo/bar', www)
    assert actual == expected

def test_virtual_path_and_indirect_neg_ext():
    www = (('%foo/bar', "Greetings program!"),)
    actual, expected = check('/greet/bar.html', '%foo/bar', www)
    assert actual == expected


# trailing slash
# ==============

def test_dispatcher_passes_through_files():
    assert_raises_404('/foo/537.html', '', (('foo/index.html', "Greetings, program!"),))

def test_trailing_slash_passes_dirs_with_slash_through():
    actual, expected = check( '/foo/'
                            , '/foo/index.html'
                            , (('foo/index.html', "Greetings, program!"),)
                             )
    assert actual == expected

def test_dispatcher_passes_through_virtual_dir_with_trailing_slash():
    actual, expected = check( '/foo/'
                            , '/%foo/index.html'
                            , (('%foo/index.html', "Greetings, program!"),)
                             )
    assert actual == expected

def test_dispatcher_redirects_dir_without_trailing_slash():
    response = raises(Response, check, '/foo', '', ('foo',)).value
    expected = (302, '/foo/')
    actual = (response.code, response.headers['Location'])
    assert actual == expected

def test_dispatcher_redirects_virtual_dir_without_trailing_slash():
    response = raises(Response, check, '/foo', '', ('%foo',)).value
    expected = (302, '/foo/')
    actual = (response.code, response.headers['Location'])
    assert actual == expected

def test_trailing_on_virtual_paths_missing():
    response = raises(Response, check, '/foo/bar/baz', '', ('%foo/%bar/%baz',)).value
    expected = '/foo/bar/baz/'
    actual = response.headers['Location']
    assert actual == expected

def test_trailing_on_virtual_paths():
    actual, expected = check( '/foo/bar/baz/'
                            , '/%foo/%bar/%baz/index.html'
                            , (('%foo/%bar/%baz/index.html', "Greetings program!"),)
                             )
    assert actual == expected

def test_dont_confuse_files_for_dirs():
    www = (('foo.html', 'Greetings, Program!'),)
    assert_raises_404('/foo.html/bar', '', www)


# path part params
# ================

def test_path_part_with_params_works():
    actual, expected = check( '/foo;a=1/'
                            , '/foo/index.html'
                            , (('foo/index.html', "Greetings program!"),)
                             )
    assert actual == expected

def test_path_part_params_vpath():
    actual, expected = check( '/foo;a=1;b=;a=2;b=3/'
                            , '/%bar/index.html'
                            , (('%bar/index.html', "Greetings program!"),)
                             )
    assert actual == expected

def test_path_part_params_static_file():
    actual, expected = check( '/foo/bar.html;a=1;b=;a=2;b=3'
                            , '/foo/bar.html'
                            , (('/foo/bar.html', "Greetings program!"),)
                             )
    assert actual == expected

def test_path_part_params_simplate():
    actual, expected = check( '/foo/bar.html;a=1;b=;a=2;b=3'
                            , '/foo/bar.html.spt'
                            , (('/foo/bar.html.spt', "Greetings program!"),)
                             )
    assert actual == expected

def test_path_part_params_negotiated_simplate():
    actual, expected = check( '/foo/bar.html;a=1;b=;a=2;b=3'
                            , '/foo/bar.spt'
                            , (('/foo/bar.spt', "Greetings program!"),)
                             )
    assert actual == expected

def test_path_part_params_greedy_simplate():
    actual, expected = check( '/foo/baz/buz;a=1;b=;a=2;b=3/blam.html'
                            , '/foo/%bar.spt'
                            , (('/foo/%bar.spt', "Greetings program!"),)
                             )
    assert actual == expected


# Docs
# ====

GREETINGS_NAME_SPT = """
[-----]
name = path['name']
[------]
Greetings, %(name)s!"""

def test_virtual_path_docs_1():
    www = (('%name/index.html.spt', GREETINGS_NAME_SPT),)
    actual, expected = handle('/aspen/', 'Greetings, aspen!', www, want='response.body')
    assert actual == expected

def test_virtual_path_docs_2():
    www = (('%name/index.html.spt', GREETINGS_NAME_SPT),)
    actual, expected = handle('/python/', 'Greetings, python!', www, want='response.body')
    assert actual == expected

NAME_LIKES_CHEESE_SPT = """
name = path['name'].title()
cheese = path['cheese']
[---------]
%(name)s likes %(cheese)s cheese."""

def test_virtual_path_docs_3():
    www = ( ( '%name/index.html.spt', GREETINGS_NAME_SPT)
          , ( '%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
           )
    actual, expected = handle( '/chad/cheddar.txt'
                             , "Chad likes cheddar cheese."
                             , www
                             , want='response.body'
                              )
    assert actual == expected

def test_virtual_path_docs_4():
    www = ( ('%name/index.html.spt', GREETINGS_NAME_SPT)
          , ('%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
           )
    actual, expected = handle('/chad/cheddar.txt/', 404, www, want='response.code')
    assert actual == expected

PARTY_LIKE_YEAR_SPT = "year = path['year']\n[----------]\nTonight we're going to party like it's %(year)s!"

def test_virtual_path_docs_5():
    www = ( ('%name/index.html.spt', GREETINGS_NAME_SPT)
          , ('%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
          , ('%year.int/index.html.spt', PARTY_LIKE_YEAR_SPT)
           )
    actual, expected = handle('/1999/', 'Greetings, 1999!', www, want='response.body')
    assert actual == expected

def test_virtual_path_docs_6():
    www = (('%year.int/index.html.spt', PARTY_LIKE_YEAR_SPT),)
    actual, expected = handle( '/1999/'
                             , "Tonight we're going to party like it's 1999!"
                             , www
                             , want='response.body'
                              )
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

def test_virtual_path_parts_can_be_empty():
    actual, expected = check( '/foo//'
                            , {u'bar': [u'']}
                            , (('foo/%bar/index.html.spt', "Greetings, program!"),)
                            , want='request.line.uri.path'
                             )
    assert actual == expected

def test_file_matches_in_face_of_dir():
    www = ( ('%page/index.html.spt', 'Nothing to see here.')
          , ('%value.txt.spt', "Greetings, program!")
           )
    actual, expected = check( '/baz.txt'
                            , {'value': [u'baz']}
                            , www
                            , want='request.line.uri.path'
                             )
    assert actual == expected

def test_file_matches_extension():
    www = ( ('%value.json.spt', '{"Greetings,": "program!"}')
          , ('%value.txt.spt', "Greetings, program!")
           )
    actual, expected = check('/baz.json', "%value.json.spt", www, want='request.fs')
    assert actual == expected

def test_file_matches_other_extension():
    www = ( ('%value.json.spt', '{"Greetings,": "program!"}')
          , ('%value.txt.spt', "Greetings, program!")
           )
    actual, expected = check('/baz.txt', "%value.txt.spt", www, want='request.fs')
    assert actual == expected

def test_virtual_file_with_no_extension_works():
    check('/baz.txt', '', (('%value.spt', '{"Greetings,": "program!"}'),))
    assert 1  # no exception

def test_normal_file_with_no_extension_works():
    www = ( ('%value.spt', '{"Greetings,": "program!"}')
          , ('value', '{"Greetings,": "program!"}')
           )
    check('/baz.txt', '', www)
    assert 1  # no exception

def test_file_with_no_extension_matches():
    www = ( ('%value.spt', '{"Greetings,": "program!"}')
          , ('value', '{"Greetings,": "program!"}')
           )
    actual = check('/baz', '', www, want='request.line.uri.path')[0]
    expected = {'value': [u'baz']}
    assert actual == expected

def test_aspen_favicon_doesnt_get_clobbered_by_virtual_path():
    actual, expected = check( '/favicon.ico'
                            , 'favicon.ico'
                            , (('%value.spt', ''),)
                            , want='request.fs'
                             )
    assert actual == expected

def test_robots_txt_also_shouldnt_be_redirected():
    assert_raises_404('/robots.txt', '', (('%value.spt', ''),))

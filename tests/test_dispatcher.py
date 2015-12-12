from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from pytest import raises

from aspen.processor import dispatcher, typecasting


# Helpers
# =======

def assert_fs(harness, ask_uri, expect_fs):
    actual = harness.simple(uripath=ask_uri, filepath=None, want='dispatch_result.match')
    assert actual == harness.fs.www.resolve(expect_fs)

def assert_raises_NotFound(*args):
    if len(args) < 3: args += ('',)
    return raises(dispatcher.NotFound, assert_fs, *args).value

def assert_raises_Redirect(*args):
    if len(args) < 3: args += ('',)
    return raises(dispatcher.Redirect, assert_fs, *args).value

def assert_virtvals(harness, uripath, expected_vals):
    actual = harness.simple(filepath=None, uripath=uripath, want='path')
    assert actual == expected_vals

def assert_body(harness, uripath, expected_body):
    actual = harness.simple(filepath=None, uripath=uripath, want='output.body')
    assert actual == expected_body

NEGOTIATED_SIMPLATE="""[-----]
[-----] text/plain
Greetings, program!
[-----] text/html
<h1>Greetings, Program!</h1>"""


# dispatcher.dispatch
# ===================

def test_dispatcher_returns_a_result(harness):
    harness.fs.www.mk(('index.html', 'Greetings, program!'),)
    result = dispatcher.dispatch( indices               = ['index.html']
                                , media_type_default    = ''
                                , pathparts             = ['']
                                , uripath               = '/'
                                , startdir              = harness.fs.www.root
                                 )
    assert result.status == dispatcher.DispatchStatus.okay
    assert result.match == os.path.join(harness.fs.www.root, 'index.html')
    assert result.wildcards == {}
    assert result.detail == 'Found.'

def test_dispatcher_raises_for_unindexed_directory(harness):
    with raises(dispatcher.UnindexedDirectory):
        dispatcher.dispatch( indices               = []
                           , media_type_default    = ''
                           , pathparts             = ['']
                           , uripath               = '/'
                           , startdir              = harness.fs.www.root
                            )


# Indices
# =======

def test_index_is_found(harness):
    expected = harness.fs.www.resolve('index.html')
    actual = harness.make_dispatch_result('Greetings, program!', 'index.html').match
    assert actual == expected

def test_negotiated_index_is_found(harness):
    expected = harness.fs.www.resolve('index')
    actual = harness.make_dispatch_result('''
        [----------] text/html
        <h1>Greetings, program!</h1>
        [----------] text/plain
        Greetings, program!
    ''', 'index').match
    assert actual == expected

def test_alternate_index_is_not_found(harness):
    assert_raises_NotFound(harness, '/')

def test_alternate_index_is_found(harness):
    harness.processor.indices += ["default.html"]
    harness.fs.www.mk(('default.html', "Greetings, program!"),)
    assert_fs(harness, '/', 'default.html')

def test_configure_aspen_py_setting_override_works_too(harness):
    harness.processor.indices = ["default.html"]
    harness.fs.www.mk(('index.html', "Greetings, program!"),)
    assert_raises_NotFound(harness, '/')

def test_configure_aspen_py_setting_takes_first(harness):
    harness.processor.indices = ["index.html", "default.html"]
    harness.fs.www.mk( ('index.html', "Greetings, program!")
                     , ('default.html', "Greetings, program!")
                      )
    assert_fs(harness, '/', 'index.html')

def test_configure_aspen_py_setting_takes_second_if_first_is_missing(harness):
    harness.processor.indices = ["index.html", "default.html"]
    harness.fs.www.mk(('default.html', "Greetings, program!"),)
    assert_fs(harness, '/', 'default.html')

def test_configure_aspen_py_setting_strips_commas(harness):
    harness.processor.indices = ["index.html", "default.html"]
    harness.fs.www.mk(('default.html', "Greetings, program!"),)
    assert_fs(harness, '/', 'default.html')

def test_redirect_indices_to_slash(harness):
    harness.processor.indices = ["index.html", "default.html"]
    harness.fs.www.mk(('index.html', "Greetings, program!"),)
    assert_raises_Redirect(harness, '/index.html')

def test_redirect_second_index_to_slash(harness):
    harness.processor.indices = ["index.html", "default.html"]
    harness.fs.www.mk(('default.html', "Greetings, program!"),)
    assert_raises_Redirect(harness, '/default.html')

def test_dont_redirect_second_index_if_first(harness):
    harness.processor.indices = ["index.html", "default.html"]
    harness.fs.www.mk(('default.html', "Greetings, program!"), ('index.html', "Greetings, program!"),)
    # first index redirects
    assert_raises_Redirect(harness, '/index.html')
    # second shouldn't
    assert_fs(harness, '/default.html', 'default.html')


# Negotiated Fall-through
# =======================

def test_indirect_negotiation_can_passthrough_static(harness):
    harness.fs.www.mk(('foo.html', "Greetings, program!"),)
    assert_fs(harness, 'foo.html', 'foo.html')

def test_indirect_negotiation_can_passthrough_renderered(harness):
    harness.fs.www.mk(('foo.html.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, 'foo.html', 'foo.html.spt')

def test_indirect_negotiation_can_passthrough_negotiated(harness):
    harness.fs.www.mk(('foo', "Greetings, program!"),)
    assert_fs(harness, 'foo', 'foo')

def test_indirect_negotiation_modifies_one_dot(harness):
    harness.fs.www.mk(('foo.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, 'foo.html', 'foo.spt')

def test_indirect_negotiation_skips_two_dots(harness):
    harness.fs.www.mk(('foo.bar.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, 'foo.bar.html', 'foo.bar.spt')

def test_indirect_negotiation_prefers_rendered(harness):
    harness.fs.www.mk( ('foo.html', "Greetings, program!")
          , ('foo', "blah blah blah")
           )
    assert_fs(harness, 'foo.html', 'foo.html')

def test_indirect_negotiation_really_prefers_rendered(harness):
    harness.fs.www.mk( ('foo.html', "Greetings, program!")
          , ('foo.', "blah blah blah")
           )
    assert_fs(harness, 'foo.html', 'foo.html')

def test_indirect_negotiation_really_prefers_rendered_2(harness):
    harness.fs.www.mk( ('foo.html', "Greetings, program!")
          , ('foo', "blah blah blah")
           )
    assert_fs(harness, 'foo.html', 'foo.html')

def test_indirect_negotation_doesnt_do_dirs(harness):
    assert_raises_NotFound(harness, 'foo.html')


# Virtual Paths
# =============

def test_virtual_path_can_passthrough(harness):
    harness.fs.www.mk(('foo.html', "Greetings, program!"),)
    assert_fs(harness, 'foo.html', 'foo.html')

def test_unfound_virtual_path_passes_through(harness):
    harness.fs.www.mk(('%bar/foo.html', "Greetings, program!"),)
    assert_raises_NotFound(harness, '/blah/flah.html')

def test_virtual_path_is_virtual(harness):
    harness.fs.www.mk(('%bar/foo.html', "Greetings, program!"),)
    assert_fs(harness, '/blah/foo.html', '%bar/foo.html')

def test_virtual_path_sets_path(harness):
    harness.fs.www.mk(('%bar/foo.spt', NEGOTIATED_SIMPLATE),)
    assert_virtvals(harness, '/blah/foo.html', {'bar': [u'blah']} )

def test_virtual_path_sets_unicode_path(harness):
    harness.fs.www.mk(('%bar/foo.html', "Greetings, program!"),)
    assert_virtvals(harness, b'/%E2%98%83/foo.html', {'bar': [u'\u2603']})

def test_virtual_path_typecasts_to_int(harness):
    harness.fs.www.mk(('%year.int/foo.html', "Greetings, program!"),)
    assert_virtvals(harness, '/1999/foo.html', {'year': [1999]})

def test_virtual_path_raises_on_bad_typecast(harness):
    harness.fs.www.mk(('%year.int/foo.html', "Greetings, program!"),)
    raises(typecasting.TypecastError, assert_fs, harness, '/I am not a year./foo.html', '')

def test_virtual_path_raises_on_direct_access(harness):
    assert_raises_NotFound(harness, '/%name/foo.html', '')

def test_virtual_path_raises_404_on_direct_access(harness):
    assert_raises_NotFound(harness, '/%name/foo.html')

def test_virtual_path_matches_the_first(harness):
    harness.fs.www.mk( ('%first/foo.html', "Greetings, program!")
          , ('%second/foo.html', "WWAAAAAAAAAAAA!!!!!!!!")
           )
    assert_fs(harness, '/1999/foo.html', '%first/foo.html')

def test_virtual_path_directory(harness):
    harness.fs.www.mk(('%first/index.html', "Greetings, program!"),)
    assert_fs(harness, '/foo/', '%first/index.html')

def test_virtual_path_file(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, '/foo/blah.html', 'foo/%bar.html.spt')

def test_virtual_path_file_only_last_part(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, '/foo/blah/baz.html', 'foo/%bar.html.spt')

def test_virtual_path_file_only_last_part____no_really(harness):
    harness.fs.www.mk(('foo/%bar.html', "Greetings, program!"),)
    assert_raises_NotFound(harness, '/foo/blah.html/')

def test_virtual_path_file_key_val_set(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_virtvals(harness, '/foo/blah.html', {'bar': [u'blah']})

def test_virtual_path_file_key_val_not_cast(harness):
    harness.fs.www.mk(('foo/%bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_virtvals(harness, '/foo/537.html', {'bar': [u'537']})

def test_virtual_path_file_key_val_cast(harness):
    harness.fs.www.mk(('foo/%bar.int.html.spt', NEGOTIATED_SIMPLATE),)
    assert_virtvals(harness, '/foo/537.html', {'bar': [537]})

def test_virtual_path_file_key_val_percent(harness):
    harness.fs.www.mk(('foo/%bar.spt', NEGOTIATED_SIMPLATE),)
    assert_virtvals(harness, '/foo/%25blah', {'bar': [u'%blah']})

def test_virtual_path_file_not_dir(harness):
    harness.fs.www.mk( ('%foo/bar.html', "Greetings from bar!")
          , ('%baz.html.spt', NEGOTIATED_SIMPLATE)
           )
    assert_fs(harness, '/bal.html', '%baz.html.spt')

# custom cast

class User:

    def __init__(self, name):
        self.username = name

    @classmethod
    def toUser(cls, name, context):
        return cls(name)

def test_virtual_path_file_key_val_cast_custom(harness):
    harness.processor.typecasters['user'] = User.toUser
    harness.fs.www.mk(( 'user/%user.user.html.spt'
                      , "[-----]\nusername=path['user']\n[-----]\nGreetings, %(username)s!"
                       ),)
    actual = harness.simple(filepath=None, uripath='/user/chad.html', want='path',
            run_through='apply_typecasters_to_path')
    assert actual['user'].username == 'chad'

# negotiated *and* virtual paths
# ==============================

def test_virtual_path__and_indirect_neg_file_not_dir(harness):
    harness.fs.www.mk( ('%foo/bar.html', "Greetings from bar!")
          , ('%baz.spt', NEGOTIATED_SIMPLATE)
           )
    assert_fs(harness, '/bal.html', '%baz.spt')

def test_virtual_path_and_indirect_neg_noext(harness):
    harness.fs.www.mk(('%foo/bar', "Greetings program!"),)
    assert_fs(harness, '/greet/bar', '%foo/bar')

def test_virtual_path_and_indirect_neg_ext(harness):
    harness.fs.www.mk(('%foo/bar.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, '/greet/bar.html', '%foo/bar.spt')


# trailing slash
# ==============

def test_dispatcher_passes_through_files(harness):
    harness.fs.www.mk(('foo/index.html', "Greetings, program!"),)
    assert_raises_NotFound(harness, '/foo/537.html')

def test_trailing_slash_passes_dirs_with_slash_through(harness):
    harness.fs.www.mk(('foo/index.html', "Greetings, program!"),)
    assert_fs(harness, '/foo/', '/foo/index.html')

def test_dispatcher_passes_through_virtual_dir_with_trailing_slash(harness):
    harness.fs.www.mk(('%foo/index.html', "Greetings, program!"),)
    assert_fs(harness, '/foo/', '/%foo/index.html')

def test_dispatcher_redirects_dir_without_trailing_slash(harness):
    harness.fs.www.mk('foo',)
    result = assert_raises_Redirect(harness, '/foo')
    assert result.message == '/foo/'

def test_dispatcher_redirects_virtual_dir_without_trailing_slash(harness):
    harness.fs.www.mk('%foo',)
    result = assert_raises_Redirect(harness, '/foo')
    assert result.message == '/foo/'

def test_trailing_on_virtual_paths_missing(harness):
    harness.fs.www.mk('%foo/%bar/%baz',)
    result = assert_raises_Redirect(harness, '/foo/bar/baz')
    assert result.message == '/foo/bar/baz/'

def test_trailing_on_virtual_paths(harness):
    harness.fs.www.mk(('%foo/%bar/%baz/index.html', "Greetings program!"),)
    assert_fs(harness, '/foo/bar/baz/', '/%foo/%bar/%baz/index.html')

def test_dont_confuse_files_for_dirs(harness):
    harness.fs.www.mk(('foo.html', 'Greetings, Program!'),)
    assert_raises_NotFound(harness, '/foo.html/bar')


# path part params
# ================

def test_path_part_with_params_works(harness):
    harness.fs.www.mk(('foo/index.html', "Greetings program!"),)
    assert_fs(harness, '/foo;a=1/', '/foo/index.html')

def test_path_part_params_vpath(harness):
    harness.fs.www.mk(('%bar/index.html', "Greetings program!"),)
    assert_fs(harness, '/foo;a=1;b=;a=2;b=3/', '/%bar/index.html')

def test_path_part_params_static_file(harness):
    harness.fs.www.mk(('/foo/bar.html', "Greetings program!"),)
    assert_fs(harness, '/foo/bar.html;a=1;b=;a=2;b=3', '/foo/bar.html')

def test_path_part_params_simplate(harness):
    harness.fs.www.mk(('/foo/bar.html.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, '/foo/bar.html;a=1;b=;a=2;b=3', '/foo/bar.html.spt')

def test_path_part_params_negotiated_simplate(harness):
    harness.fs.www.mk(('/foo/bar.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, '/foo/bar.txt;a=1;b=;a=2;b=3', '/foo/bar.spt')

def test_path_part_params_greedy_simplate(harness):
    harness.fs.www.mk(('/foo/%bar.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, '/foo/baz/buz;a=1;b=;a=2;b=3/blam.html', '/foo/%bar.spt')


# Docs
# ====

GREETINGS_NAME_SPT = """
[-----]
name = path['name']
[------]
Greetings, %(name)s!"""

def test_virtual_path_docs_1(harness):
    harness.fs.www.mk(('%name/index.html.spt', GREETINGS_NAME_SPT),)
    assert_body(harness, '/aspen/', 'Greetings, aspen!')

def test_virtual_path_docs_2(harness):
    harness.fs.www.mk(('%name/index.html.spt', GREETINGS_NAME_SPT),)
    assert_body(harness, '/python/', 'Greetings, python!')

NAME_LIKES_CHEESE_SPT = """
[-----]
name = path['name'].title()
cheese = path['cheese']
[---------]
%(name)s likes %(cheese)s cheese."""

def test_virtual_path_docs_3(harness):
    harness.fs.www.mk( ( '%name/index.html.spt', GREETINGS_NAME_SPT)
          , ( '%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
           )
    assert_body(harness, '/chad/cheddar.txt', "Chad likes cheddar cheese.")

def test_virtual_path_docs_4(harness):
    harness.fs.www.mk( ('%name/index.html.spt', GREETINGS_NAME_SPT)
          , ('%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
           )
    assert_raises_NotFound(harness, '/chad/cheddar.txt/')

PARTY_LIKE_YEAR_SPT = """\
[-----]
year = path['year']
[----------]
Tonight we're going to party like it's %(year)s!"""

def test_virtual_path_docs_5(harness):
    harness.fs.www.mk( ('%name/index.html.spt', GREETINGS_NAME_SPT)
          , ('%name/%cheese.txt.spt', NAME_LIKES_CHEESE_SPT)
          , ('%year.int/index.html.spt', PARTY_LIKE_YEAR_SPT)
           )
    assert_body(harness, '/1999/', 'Greetings, 1999!')

def test_virtual_path_docs_6(harness):
    harness.fs.www.mk(('%year.int/index.html.spt', PARTY_LIKE_YEAR_SPT),)
    assert_body(harness, '/1999/', "Tonight we're going to party like it's 1999!")


# mongs
# =====
# These surfaced when porting mongs from Aspen 0.8.

def test_virtual_path_parts_can_be_empty(harness):
    harness.fs.www.mk(('foo/%bar/index.html.spt', NEGOTIATED_SIMPLATE),)
    assert_virtvals(harness, '/foo//' , {u'bar': [u'']})

def test_file_matches_in_face_of_dir(harness):
    harness.fs.www.mk( ('%page/index.html.spt', NEGOTIATED_SIMPLATE)
          , ('%value.txt.spt', NEGOTIATED_SIMPLATE)
           )
    assert_virtvals(harness, '/baz.txt', {'value': [u'baz']})

def test_file_matches_extension(harness):
    harness.fs.www.mk( ('%value.json.spt', '[-----]\n[-----]\n{"Greetings,": "program!"}')
          , ('%value.txt.spt', NEGOTIATED_SIMPLATE)
           )
    assert_fs(harness, '/baz.json', "%value.json.spt")

def test_file_matches_other_extension(harness):
    harness.fs.www.mk( ('%value.json.spt', '[-----]\n[-----]\n{"Greetings,": "program!"}')
          , ('%value.txt.spt', NEGOTIATED_SIMPLATE)
           )
    assert_fs(harness, '/baz.txt', "%value.txt.spt")


def test_virtual_file_with_no_extension_works(harness):
    harness.fs.www.mk(('%value.spt', NEGOTIATED_SIMPLATE),)
    assert_fs(harness, '/baz.txt', '%value.spt')

def test_normal_file_with_no_extension_works(harness):
    harness.fs.www.mk( ('%value.spt', NEGOTIATED_SIMPLATE)
          , ('value', '{"Greetings,": "program!"}')
           )
    assert_fs(harness, '/baz.txt', '%value.spt')

def test_file_with_no_extension_matches(harness):
    harness.fs.www.mk( ('%value.spt', NEGOTIATED_SIMPLATE)
          , ('value', '{"Greetings,": "program!"}')
           )
    assert_fs(harness, '/baz', '%value.spt')
    assert_virtvals(harness, '/baz', {'value': [u'baz']})

def test_dont_serve_hidden_files(harness):
    harness.fs.www.mk(('.secret_data', ''),)
    assert_raises_NotFound(harness, '/.secret_data')

def test_dont_serve_spt_file_source(harness):
    harness.fs.www.mk(('foo.html.spt', "Greetings, program!"),)
    assert_raises_NotFound(harness, '/foo.html.spt')

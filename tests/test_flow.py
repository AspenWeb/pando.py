from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from aspen.flow import Flow, FunctionNotFound


# parse_signature
# ===============

def test_parse_signature_infers_defaults():
    def func(foo='bar'): pass
    names, required, optional = Flow._parse_signature(func)
    assert names == ('foo',)
    assert required == tuple()
    assert optional == {'foo': 'bar'}

def test_parse_signature_returns_empty_dict_for_no_defaults():
    def func(foo, bar, baz): pass
    names, required, optional = Flow._parse_signature(func)
    assert names == ('foo', 'bar', 'baz')
    assert required == ('foo', 'bar', 'baz')
    assert optional == {}

def test_parse_signature_works_with_mixed_arg_kwarg():
    def func(foo, bar, baz='buz'): pass
    names, required, optional = Flow._parse_signature(func)
    assert names == ('foo', 'bar', 'baz')
    assert required == ('foo', 'bar')
    assert optional == {'baz': 'buz'}

def test_parse_signature_doesnt_conflate_objects_defined_inside():
    def func(foo, bar, baz=2):
        blah = foo * 42
        return blah
    names, required, optional = Flow._parse_signature(func)
    assert names == ('foo', 'bar', 'baz')
    assert required == ('foo', 'bar')
    assert optional == {'baz': 2}


# resolve_dependencies
# ====================

def test_resolve_dependencies_resolves_dependencies():
    def func(foo): pass
    deps = Flow._resolve_dependencies(func, {'foo': 1})
    assert deps.names == ('foo',)
    assert deps.required == ('foo',)
    assert deps.optional == {}
    assert deps.a == (1,)
    assert deps.kw == {'foo': 1}

def test_resolve_dependencies_resolves_two_dependencies():
    def func(foo, bar): pass
    deps = Flow._resolve_dependencies(func, {'foo': 1, 'bar': True})
    assert deps.a == (1, True)
    assert deps.kw == {'foo': 1, 'bar': True}

def test_resolve_dependencies_resolves_kwarg():
    def func(foo, bar=False): pass
    deps = Flow._resolve_dependencies(func, {'foo': 1, 'bar': True})
    assert deps.a == (1, True)
    assert deps.kw == {'foo': 1, 'bar': True}

def test_resolve_dependencies_honors_kwarg_default():
    def func(foo, bar=False): pass
    deps = Flow._resolve_dependencies(func, {'foo': 1})
    assert deps.a == (1, False)
    assert deps.kw == {'foo': 1, 'bar': False}

def test_resolve_dependencies_honors_kwarg_default_of_None():
    def func(foo, bar=None): pass
    deps = Flow._resolve_dependencies(func, {'foo': 1})
    assert deps.a == (1, None)
    assert deps.kw == {'foo': 1, 'bar': None}

def test_resolve_dependencies_doesnt_get_hung_up_on_None_though():
    def func(foo, bar=None): pass
    deps = Flow._resolve_dependencies(func, {'foo': 1, 'bar': True})
    assert deps.a == (1, True)
    assert deps.kw == {'foo': 1, 'bar': True}


# Flow
# ====

def test_Flow_can_be_instantiated(sys_path):
    sys_path.mk(('foo/__init__.py', ''), ('foo/bar.py', 'def baz(): pass'))
    bar_flow = Flow('foo.bar')
    from foo.bar import baz
    assert list(bar_flow) == [baz]

def test_Flow_includes_imported_functions_and_the_order_is_screwy(sys_path):
    sys_path.mk( ('um.py', 'def um(): pass')
               , ('foo/__init__.py', '')
               , ('foo/bar.py', '''
def baz(): pass
from um import um
def blah(): pass
'''))
    bar_flow = Flow('foo.bar')
    import foo.bar, um
    assert list(bar_flow) == [um.um, foo.bar.baz, foo.bar.blah]

def test_Flow_ignores_functions_starting_with_underscore(sys_path):
    sys_path.mk( ('um.py', 'def um(): pass')
               , ('foo/__init__.py', '')
               , ('foo/bar.py', '''
def baz(): pass
from um import um as _um
def blah(): pass
'''))
    bar_flow = Flow('foo.bar')
    import foo.bar
    assert list(bar_flow) == [foo.bar.baz, foo.bar.blah]

def test_can_run_through_flow(sys_path):
    sys_path.mk(('foo.py', '''
def bar(): return {'val': 1}
def baz(): return {'val': 2}
def buz(): return {'val': 3}
'''))
    bar_flow = Flow('foo')
    state = bar_flow.run({'val': None})
    assert state == {'val': 3, 'exc_info': None, 'state': state}

def test_can_run_through_flow_to_a_certain_point(sys_path):
    sys_path.mk(('foo.py', '''
def bar(): return {'val': 1}
def baz(): return {'val': 2}
def buz(): return {'val': 3}
'''))
    bar_flow = Flow('foo')
    state = bar_flow.run({'val': None}, through='baz')
    assert state == {'val': 2, 'exc_info': None, 'state': state}

def test_error_raised_if_we_try_to_run_through_an_unknown_function(sys_path):
    sys_path.mk(('foo.py', '''
def bar(): return {'val': 1}
def baz(): return {'val': 2}
def buz(): return {'val': 3}
'''))
    bar_flow = Flow('foo')
    pytest.raises(FunctionNotFound, bar_flow.run, {'val': None}, through='blaaaaaah')

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import flow


# parse_signature
# ===============

def test_parse_signature_infers_defaults():
    def func(foo='bar'): pass
    names, required, optional = flow.parse_signature(func)
    assert names == ('foo',)
    assert required == tuple()
    assert optional == {'foo': 'bar'}

def test_parse_signature_returns_empty_dict_for_no_defaults():
    def func(foo, bar, baz): pass
    names, required, optional = flow.parse_signature(func)
    assert names == ('foo', 'bar', 'baz')
    assert required == ('foo', 'bar', 'baz')
    assert optional == {}

def test_parse_signature_works_with_mixed_arg_kwarg():
    def func(foo, bar, baz='buz'): pass
    names, required, optional = flow.parse_signature(func)
    assert names == ('foo', 'bar', 'baz')
    assert required == ('foo', 'bar')
    assert optional == {'baz': 'buz'}

def test_parse_signature_doesnt_conflate_objects_defined_inside():
    def func(foo, bar, baz=2):
        blah = foo * 42
        return blah
    names, required, optional = flow.parse_signature(func)
    assert names == ('foo', 'bar', 'baz')
    assert required == ('foo', 'bar')
    assert optional == {'baz': 2}


# resolve_dependencies
# ====================

def test_resolve_dependencies_resolves_dependencies():
    def func(foo): pass
    deps = flow.resolve_dependencies(func, {'foo': 1})
    assert deps.names == ('foo',)
    assert deps.required == ('foo',)
    assert deps.optional == {}
    assert deps.a == (1,)
    assert deps.kw == {'foo': 1}

def test_resolve_dependencies_resolves_two_dependencies():
    def func(foo, bar): pass
    deps = flow.resolve_dependencies(func, {'foo': 1, 'bar': True})
    assert deps.a == (1, True)
    assert deps.kw == {'foo': 1, 'bar': True}

def test_resolve_dependencies_resolves_kwarg():
    def func(foo, bar=False): pass
    deps = flow.resolve_dependencies(func, {'foo': 1, 'bar': True})
    assert deps.a == (1, True)
    assert deps.kw == {'foo': 1, 'bar': True}

def test_resolve_dependencies_honors_kwarg_default():
    def func(foo, bar=False): pass
    deps = flow.resolve_dependencies(func, {'foo': 1})
    assert deps.a == (1, False)
    assert deps.kw == {'foo': 1, 'bar': False}

def test_resolve_dependencies_honors_kwarg_default_of_None():
    def func(foo, bar=None): pass
    deps = flow.resolve_dependencies(func, {'foo': 1})
    assert deps.a == (1, None)
    assert deps.kw == {'foo': 1, 'bar': None}

def test_resolve_dependencies_doesnt_get_hung_up_on_None_though():
    def func(foo, bar=None): pass
    deps = flow.resolve_dependencies(func, {'foo': 1, 'bar': True})
    assert deps.a == (1, True)
    assert deps.kw == {'foo': 1, 'bar': True}

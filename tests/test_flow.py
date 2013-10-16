from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import flow


# parse_signature
# ===============

def test_parse_signature_infers_defaults():
    def func(foo='bar'): pass
    required, optional = flow.parse_signature(func)
    assert required == tuple()
    assert optional == {'foo': 'bar'}

def test_parse_signature_returns_empty_dict_for_no_defaults():
    def func(foo, bar, baz): pass
    required, optional = flow.parse_signature(func)
    assert required == ('foo', 'bar', 'baz')
    assert optional == {}

def test_parse_signature_works_with_mixed_arg_kwarg():
    def func(foo, bar, baz='buz'): pass
    required, optional = flow.parse_signature(func)
    assert required == ('foo', 'bar')
    assert optional == {'baz': 'buz'}


# inject_dependencies
# ===================

def test_inject_dependencies_injects_dependencies():
    def func(foo): pass
    kw = flow.inject_dependencies(func, {'foo': 1})
    assert kw == {'foo': 1}

def test_inject_dependencies_injects_two_dependencies():
    def func(foo, bar): pass
    kw = flow.inject_dependencies(func, {'foo': 1, 'bar': True})
    assert kw == {'foo': 1, 'bar': True}

def test_inject_dependencies_injects_kwarg():
    def func(foo, bar=False): pass
    kw = flow.inject_dependencies(func, {'foo': 1, 'bar': True})
    assert kw == {'foo': 1, 'bar': True}

def test_inject_dependencies_honors_kwarg_default():
    def func(foo, bar=False): pass
    kw = flow.inject_dependencies(func, {'foo': 1})
    assert kw == {'foo': 1, 'bar': False}

def test_inject_dependencies_honors_kwarg_default_of_None():
    def func(foo, bar=None): pass
    kw = flow.inject_dependencies(func, {'foo': 1})
    assert kw == {'foo': 1, 'bar': None}

def test_inject_dependencies_doesnt_get_hung_up_on_None_though():
    def func(foo, bar=None): pass
    kw = flow.inject_dependencies(func, {'foo': 1, 'bar': True})
    assert kw == {'foo': 1, 'bar': True}

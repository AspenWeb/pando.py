from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple


# Dependency Injection Helpers
# ============================

def parse_signature(function):
    """Given a function, return a tuple of required args and dict of optional args.
    """
    code = function.func_code
    varnames = code.co_varnames[:code.co_argcount]

    nrequired = len(varnames)
    values = function.func_defaults
    optional = {}
    if values is not None:
        nrequired = -len(values)
        keys = varnames[nrequired:]
        optional = dict(zip(keys, values))

    required = varnames[:nrequired]

    return varnames, required, optional


def resolve_dependencies(function, available):
    """Given a function and a dict of available deps, return a deps object.

    The deps object has these attributes:

        a - a tuple of argument values
        kw - a dictionary of keyword arguments
        names - a tuple of the names of all arguments (in order)
        required - a tuple of names of required arguments (in order)
        optional - a dictionary of names of optional arguments with their
                     default values

    """
    deps = namedtuple('deps', 'a kw names required optional')
    deps.a = tuple()
    deps.kw = {}
    deps.names, deps.required, deps.optional = parse_signature(function)

    missing = object()
    for name in deps.names:
        value = missing  # don't use .get, to avoid bugs around None
        if name in available:
            value = available[name]
        elif name in deps.optional:
            value = deps.optional[name]
        if value is not missing:
            deps.a += (value,)
            deps.kw[name] = value
    return deps

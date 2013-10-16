from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def parse_signature(function):
    """Given a function, return a tuple of required args and dict of optional args.
    """
    varnames = function.func_code.co_varnames

    nrequired = len(varnames)
    values = function.func_defaults
    optional = {}
    if values is not None:
        nrequired = -len(values)
        keys = varnames[nrequired:]
        optional = dict(zip(keys, values))

    required = varnames[:nrequired]

    return required, optional


def resolve_dependencies(function, available):
    """Given a function and a dict of available deps, return a kwargs dict.
    """
    out = {}
    required, optional = parse_signature(function)
    missing = object()
    for name in function.func_code.co_varnames:
        value = missing
        if name in available:
            value = available[name]
        elif name in optional:
            value = optional[name]
        if value is not missing:
            out[name] = value
    return out

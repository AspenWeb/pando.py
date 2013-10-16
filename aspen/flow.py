def infer_defaults(function):
    """Given a function, return a dict of defaults for kwargs.
    """
    values = function.func_defaults
    if values is None:
        return {}
    keys = function.func_code.co_varnames[-len(values):]
    return dict(zip(keys, values))


def inject_dependencies(function, available):
    """Given a function and a state dict, return a kwargs dict.
    """
    out = {}
    defaults = infer_defaults(function)
    missing = object()
    for name in function.func_code.co_varnames:
        value = missing
        if name in available:
            value = available[name]
        elif name in defaults:
            value = defaults[name]
        if value is not missing:
            out[name] = value
    return out

import datetime

from aspen.exceptions import LoadError


# Find a json module.
# ===================
# The standard library includes simplejson as json since 2.6, but without the 
# C speedups. So we prefer simplejson if it is available.

try:
    import simplejson as _json
except ImportError:
    try:
        import json as _json
    except ImportError:
        _json = None


if _json is not None:
    class FriendlyEncoder(_json.JSONEncoder):
        """Add support for additional types to the default JSON encoder.
        """

        def default(self, obj):
            if isinstance(obj, complex):
                # http://docs.python.org/library/json.html
                out = [obj.real, obj.imag]
            elif isinstance(obj, datetime.datetime):
                # http://stackoverflow.com/questions/455580/
                out = obj.isoformat()
            else:
                out = super(FriendlyEncoder, self).default(obj)
            return out

def lazy_check(): 
    if _json is None:
        raise LoadError("Neither json nor simplejson was found. Try "
                        "installing simplejson to use dynamic JSON "
                        "resources. See "
                        "http://aspen.io/resources/json/#libraries for "
                        "more information.")

def loads(*a, **kw):
    lazy_check()
    return _json.loads(*a, **kw)

def dumps(*a, **kw):
    lazy_check()
    if 'cls' not in kw:
        kw['cls'] = FriendlyEncoder
    return _json.dumps(*a, **kw)

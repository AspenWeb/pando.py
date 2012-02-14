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


# Allow arbitrary encoders to be registered.
# ==========================================
# One of the difficulties with JSON in Python is that pretty quickly one hits a
# class or type that needs extra work to decode to JSON. For example, support
# for the decimal.Decimal class was added in simplejson 2.1, which isn't in the
# stdlib version as of 2.7/3.2. Support for classes from the datetime module
# isn't in simplejson as of 2.3.2. Since Aspen takes on ownership of JSON
# encoding, we need to give Aspen users a way to register (and unregister, I
# guess) new encoders. You can do this by calling dumps with the cls keyword,
# but we call dumps for you for JSON resources, so we want a way to influence
# decoding that doesn't depend on dumps. And this is that way:

encoders = {}
def register_encoder(cls, encode):
    """Register the encode function for cls.
    
    An encoder should take an instance of cls and return something basically
    serializable (strings, lists, dictionaries).

    """
    encoders[cls] = encode

def unregister_encoder(cls):
    """Given a class, remove any encoder that has been registered for it.
    """
    if cls in encoders:
        del encoders[cls]

# http://docs.python.org/library/json.html
register_encoder(complex, lambda obj: [obj.real, obj.imag])

# http://stackoverflow.com/questions/455580/
register_encoder(datetime.datetime, lambda obj: obj.isoformat())
register_encoder(datetime.date, lambda obj: obj.isoformat())
register_encoder(datetime.time, lambda obj: obj.isoformat())


# Be lazy.
# ========
# Allow Aspen to run without json support. In practice that means that Python
# 2.5 users won't be able to use json resources.

if _json is not None:
    class FriendlyEncoder(_json.JSONEncoder):
        """Add support for additional types to the default JSON encoder.
        """
        def default(self, obj):
            cls = obj.__class__ # Use this instead of type(obj) because that 
                                # isn't consistent between new- and old-style 
                                # classes, and this is.
            encode = encoders.get(cls, super(FriendlyEncoder, self).default)
            return encode(obj)

def lazy_check(): 
    if _json is None:
        raise ImportError("Neither simplejson nor json was found. Try "
                          "installing simplejson to use dynamic JSON "
                          "resources. See "
                          "http://aspen.io/resources/json/#libraries for "
                          "more information.")


# Main public API.
# ================

def loads(*a, **kw):
    lazy_check()
    return _json.loads(*a, **kw)

def dumps(*a, **kw):
    lazy_check()
    if 'cls' not in kw:
        kw['cls'] = FriendlyEncoder
    return _json.dumps(*a, **kw)

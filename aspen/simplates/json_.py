"""
aspen.json
++++++++++
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime


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
# Allow Aspen to run without JSON support. In practice that means that Python
# 2.5 users won't be able to use JSON resources.

if _json is not None:
    class FriendlyEncoder(_json.JSONEncoder):
        """Add support for additional types to the default JSON encoder.
        """
        def default(self, obj):
            cls = obj.__class__ # Use this instead of type(obj) because that
                                # isn't consistent between new- and old-style
                                # classes, and this is.
            encode = encoders.get(cls, _json.JSONEncoder.default)
            return encode(obj)

def lazy_check():
    if _json is None:
        raise ImportError("Neither simplejson nor json was found. Try "
                          "installing simplejson to use dynamic JSON "
                          "simplates. See "
                          "http://aspen.io/simplates/json/#libraries for "
                          "more information.")


# Main public API.
# ================

def load(*a, **kw):
    lazy_check()
    return _json.load(*a, **kw)

def dump(*a, **kw):
    lazy_check()
    if 'cls' not in kw:
        kw['cls'] = FriendlyEncoder
    # Beautify json by default.
    if 'sort_keys' not in kw:
        kw['sort_keys'] = True
    if 'indent' not in kw:
        kw['indent'] = 4
    return _json.dump(*a, **kw)

def loads(*a, **kw):
    lazy_check()
    return _json.loads(*a, **kw)

def dumps(*a, **kw):
    lazy_check()
    if 'cls' not in kw:
        kw['cls'] = FriendlyEncoder
    # Beautify json by default.
    if 'sort_keys' not in kw:
        kw['sort_keys'] = True
    if 'indent' not in kw:
        kw['indent'] = 4
    return _json.dumps(*a, **kw)


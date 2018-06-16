from __future__ import absolute_import, division, print_function, unicode_literals

try:
    from urllib.parse import quote, quote_plus
except ImportError:
    from urllib import quote as _quote, quote_plus as _quote_plus

    # Monkey-patch urllib to counter the effects of unicode_literals
    import urllib
    urllib.always_safe = urllib.always_safe.encode('ascii')
    urllib._safe_quoters.clear()

    def quote(string, safe=b'/'):
        if not isinstance(safe, bytes):
            safe = safe.encode('ascii', 'ignore')
        if not isinstance(string, bytes):
            string = string.encode('utf8')
        return _quote(string, safe)

    def quote_plus(string, safe=b''):
        if not isinstance(safe, bytes):
            safe = safe.encode('ascii', 'ignore')
        if not isinstance(string, bytes):
            string = string.encode('utf8')
        return _quote_plus(string, safe)

__all__ = [quote, quote_plus]

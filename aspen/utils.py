import codecs


# Register a 'repr' error strategy.
# =================================
# Sometimes we want to echo bytestrings back to a user, and we don't know what 
# encoding will work. This error strategy replaces non-decodable bytes with 
# their Python representation, so that they are human-visible.
# 
# See also:
#   - https://github.com/dcrosta/mongo/commit/e1ac732
#   - http://www.crummy.com/software/BeautifulSoup/bs4/doc/#unicode-dammit

def replace_with_repr(unicode_error):
    offender = unicode_error.object[unicode_error.start:unicode_error.end]
    return (unicode(repr(offender).strip("'").strip('"')), unicode_error.end)

codecs.register_error('repr', replace_with_repr)


def unicode_dammit(s, encoding="UTF-8"):
    """Given a bytestring, return a unicode decoded with `encoding`.

    Any bytes not decodable with UTF-8 will be replaced with their Python
    representation, so you'll get something like u"foo\\xefbar".

    """
    if not isinstance(s, str):
        raise TypeError("You gave me something besides a str.")
    errors = 'repr'
    return s.decode(encoding, errors)

def ascii_dammit(s):
    """Given a bytestring, return a bytestring.

    The returned bytestring will have any non-ASCII bytes replaced with
    their Python representation, so it will be pure ASCII.

    """
    return unicode_dammit(s, encoding="ASCII").encode("ASCII")

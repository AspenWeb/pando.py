"""
:mod:`exceptions`
=================

Custom exceptions raised by Pando
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from . import Response


class CRLFInjection(Response):
    """
    A 400 :py:class:`.Response` (per `#249`_) raised if there's a suspected CRLF
    Injection attack in the headers.

    .. _#249: https://github.com/AspenWeb/pando.py/issues/249
    """
    def __init__(self):
        Response.__init__(self, code=400, body="Possible CRLF Injection detected.")


class MalformedHeader(Response):
    """
    A 400 :py:class:`.Response` (per `RFC7230 section 3.2.4`_) raised if there's
    no ``:`` in a header field, or if there's leading or trailing whitespace in
    the key part of a header field.

    .. _RFC7230 section 3.2.4: http://tools.ietf.org/html/rfc7230#section-3.2.4
    """
    def __init__(self, header):
        Response.__init__(self, code=400, body="Malformed header: %s" % header)


class MalformedBody(Response):
    """
    A 400 :py:class:`.Response` raised if parsing the body of a POST request fails.
    """
    def __init__(self, msg):
        Response.__init__(self, code=400, body="Malformed body: %s" % msg)


class UnknownBodyType(Response):
    """
    A 415 :py:class:`.Response` raised if the ``Content-Type`` of the body of a
    POST request doesn't have a ``body_parser`` registered for it.
    """
    def __init__(self, ctype):
        Response.__init__(self, code=415, body="Unknown body Content-Type: %s" % ctype)


class BadLocation(Response):
    """
    A 500 :py:class:`.Response` raised if an invalid redirect is attempted.
    """
    def __init__(self, msg):
        Response.__init__(self, code=500, body="Bad redirect location: %s" % msg)

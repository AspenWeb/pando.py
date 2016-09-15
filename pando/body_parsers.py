"""
:mod:`body_parsers`
===================

This module contains Pando's built-in body parsers.

Body parsers are optional ways to enable Pando to uniformly parse POST body
content according to its supplied ``Content-Type``.

A body parser has the signature::

   def name(raw, headers):

where ``raw`` is the raw bytestring to be parsed, and ``headers`` is the
:py:class:`.Headers` mapping of the supplied headers.
"""

import cgi
from io import BytesIO

from six import PY3

from . import json
from .utils import typecheck
from .http.request import Headers
from .http.mapping import CaseInsensitiveMapping, Mapping
from .exceptions import MalformedBody, UnknownBodyType


def formdata(raw, headers):
    """Parse ``raw`` as form data.

    Supports ``application/x-www-form-urlencoded`` and ``multipart/form-data``.

    """

    # Force the cgi module to parse as we want. If it doesn't find
    # something besides GET or HEAD here then it ignores the fp
    # argument and instead uses environ['QUERY_STRING'] or even
    # sys.stdin(!). We want it to parse request bodies even if the
    # method is GET (we already parsed the querystring elsewhere).

    environ = {"REQUEST_METHOD": "POST"}
    if PY3:
        _headers = CaseInsensitiveMapping()
        for k, vals in headers.items():
            for v in vals:
                _headers.add(k.decode('ascii'), v.decode('ascii'))
        headers = _headers
    parsed = cgi.FieldStorage( fp = BytesIO(raw)  # Ack.
                             , environ = environ
                             , headers = headers
                             , keep_blank_values = True
                             , strict_parsing = False
                              )
    result = Mapping()
    for k in parsed.keys():
        vals = parsed[k]
        if not isinstance(vals, list):
            vals = [vals]
        for v in vals:
            if v.filename is None:
                v = v.value
                if isinstance(v, bytes):
                    v = v.decode("UTF-8")  # XXX Really?  Always UTF-8?
            result.add(k, v)
    return result


def jsondata(raw, headers):
    """Parse ``raw`` as JSON data."""
    try:
        return json.loads(raw.decode('utf8'))
    except UnicodeDecodeError as e:
        raise MalformedBody(str(e))


def parse_body(raw, headers, parsers):
    """Parses the ``raw`` bytestring using the ``headers`` to determine which of
    the ``parsers`` should be used.

    Raises :py:exc:`.UnknownBodyType` if the HTTP ``Content-Type`` isn't recognized,
    and :py:exc:`.MalformedBody` if the parser raises a :py:exc:`ValueError`.

    """

    typecheck(headers, Headers)

    # Note we ignore parameters for now
    content_type = headers.get(b"Content-Type", b"").split(b';')[0]
    content_type = content_type.decode('ascii', 'repr')

    def default_parser(raw, headers):
        if not content_type and not raw:
            return {}
        raise UnknownBodyType(content_type)

    try:
        return parsers.get(content_type, default_parser)(raw, headers)
    except ValueError as e:
        raise MalformedBody(str(e))

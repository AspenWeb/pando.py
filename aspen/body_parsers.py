"""
aspen.body_parsers
++++++++++++++++++

Aspen body parsers are optional ways to enable Aspen to uniformly
parse POST body content according to its supplied Content-Type.

A body parser has the signature:

   def name(raw, headers):

where _raw_ is the raw bytes to be parsed, and _headers_ is the
Headers mapping of the supplied headers
"""

import cgi
from aspen import Response, json_ as json
from aspen.utils import typecheck
from aspen.http.request import Headers
from aspen.http.mapping import Mapping
from aspen.exceptions import MalformedBody, UnknownBodyType

def formdata(raw, headers):
    """Parse raw as form data"""

    # Force the cgi module to parse as we want. If it doesn't find
    # something besides GET or HEAD here then it ignores the fp
    # argument and instead uses environ['QUERY_STRING'] or even
    # sys.stdin(!). We want it to parse request bodies even if the
    # method is GET (we already parsed the querystring elsewhere).

    environ = {"REQUEST_METHOD": "POST"}
    parsed = cgi.FieldStorage( fp = cgi.StringIO(raw)  # Ack.
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
            if isinstance(v, cgi.MiniFieldStorage):
                v = v.value.decode("UTF-8")  # XXX Really?  Always UTF-8?
            else:
                assert isinstance(v, cgi.FieldStorage), v
                if v.filename is None:
                    v = v.value.decode("UTF-8")
            result.add(k, v)
    return result


def jsondata(raw, headers):
    """Parse raw as json data"""

    return json.loads(raw)


def parse_body(raw, headers, parsers):
    """Takes a file-like object, a str, and another str.

    If the Mapping API is used (in/one/all/has), then the iterable will be
    read and parsed according to content_type.

    """

    typecheck(headers, Headers)

    # Note we ignore parameters for now
    content_type = headers.get("Content-Type", "").split(';')[0]

    def default_parser(raw, headers):
        if not content_type and not raw:
            return {}
        raise UnknownBodyType(content_type)

    try:
        return parsers.get(content_type, default_parser)(raw, headers)
    except ValueError as e:
        raise MalformedBody(str(e))

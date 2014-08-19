from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.http.request import Headers
import aspen.body_parsers as parsers


FORMDATA = object()
WWWFORM = object()

def make_body(raw, headers=None, content_type=WWWFORM):
    if isinstance(raw, unicode):
        raw = raw.encode('ascii')
    if headers is None:
        defaults = { FORMDATA: "multipart/form-data; boundary=AaB03x",
                     WWWFORM: "application/x-www-form-urlencoded" }
        headers = {"Content-Type": defaults.get(content_type, content_type)}
    if not 'content-length' in headers:
        headers['Content-length'] = str(len(raw))
    body_parsers = {
            "application/x-www-form-urlencoded": parsers.formdata,
            "multipart/form-data": parsers.formdata
    }
    headers['Host'] = 'Blah'
    return parsers.parse_body(raw, Headers(headers), body_parsers)


def test_body_is_unparsed_for_empty_content_type():
    raw = "cheese=yes"
    actual = make_body(raw, headers={})
    assert actual == raw

def test_body_barely_works():
    body = make_body("cheese=yes")
    actual = body['cheese']
    assert actual == "yes"


UPLOAD = """\
--AaB03x
Content-Disposition: form-data; name="submit-name"

Larry
--AaB03x
Content-Disposition: form-data; name="files"; filename="file1.txt"
Content-Type: text/plain

... contents of file1.txt ...
--AaB03x--
"""

def test_body_barely_works_for_form_data():
    body = make_body(UPLOAD, content_type=FORMDATA)
    actual = body['files'].filename
    assert actual == "file1.txt"

def test_simple_values_are_simple():
    body = make_body(UPLOAD, content_type=FORMDATA)
    actual = body['submit-name']
    assert actual == "Larry"

def test_params_doesnt_break_www_form():
    body = make_body("statement=foo"
                    , content_type="application/x-www-form-urlencoded; charset=UTF-8; cheese=yummy"
                     )
    actual = body['statement']
    assert actual == "foo"

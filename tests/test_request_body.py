from io import BytesIO

from pytest import raises

from pando.exceptions import MalformedBody, UnknownBodyType
from pando.http.request import Request
from pando.http.response import Response


FORMDATA = object()
WWWFORM = object()

def make_body(harness, raw, headers=None, content_type=WWWFORM):
    if not isinstance(raw, bytes):
        raw = raw.encode('ascii')
    if headers is None:
        defaults = {
            FORMDATA: b"multipart/form-data; boundary=AaB03x",
            WWWFORM: b"application/x-www-form-urlencoded",
        }
        headers = {b"Content-Type": defaults.get(content_type, content_type)}
    if b'Content-Length' not in headers:
        headers[b'Content-Length'] = str(len(raw)).encode('ascii')
    headers[b'Host'] = b'Blah'
    website = harness.client.website
    request = Request(website, body=BytesIO(raw), headers=headers)
    return request.body


def test_body_is_unparsed_for_empty_content_type(harness):
    raw = "cheese=yes"
    with raises(UnknownBodyType):
        make_body(harness, raw, headers={})

def test_body_barely_works(harness):
    body = make_body(harness, "cheese=yes")
    actual = body['cheese']
    assert actual == "yes"


UPLOAD = '\r\n'.join("""\
--AaB03x
Content-Disposition: form-data; name="submit-name"

Larry
--AaB03x
Content-Disposition: form-data; name="files"; filename="file1.txt"
Content-Type: text/plain

... contents of file1.txt ...
--AaB03x--
""".splitlines())

def test_body_barely_works_for_form_data(harness):
    body = make_body(harness, UPLOAD, content_type=FORMDATA)
    actual = body['files'].filename
    assert actual == "file1.txt"

def test_simple_values_are_simple(harness):
    body = make_body(harness, UPLOAD, content_type=FORMDATA)
    actual = body['submit-name']
    assert actual == "Larry"

def test_multiple_values_are_multiple(harness):
    body = make_body(harness, "cheese=yes&cheese=burger")
    assert body.all('cheese') == ["yes", "burger"]

def test_params_doesnt_break_www_form(harness):
    body = make_body(
        harness, "statement=foo",
        content_type=b"application/x-www-form-urlencoded; charset=UTF-8; cheese=yummy"
    )
    actual = body['statement']
    assert actual == "foo"

def test_malformed_body_jsondata(harness):
    with raises(MalformedBody):
        make_body(harness, "foo", content_type=b"application/json")

def test_malformed_body_formdata(harness):
    with raises(MalformedBody):
        make_body(harness, "", content_type=b"multipart/form-data; boundary=\0")

def test_bad_content_length(harness):
    with raises(Response) as x:
        make_body(harness, "{}", headers={
            b'Content-Length': b'NaN',
            b'Content-Type': b'application/json',
        })
    assert x.value.code == 400

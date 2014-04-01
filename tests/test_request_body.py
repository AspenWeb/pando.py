from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from StringIO import StringIO

from aspen.http.request import Body, Headers

FORMDATA = object()
WWWFORM = object()

def make_body(raw, headers=None, content_type=WWWFORM):
    if isinstance(raw, unicode):
        raw = raw.encode('ascii')
    if headers is None:
        if content_type is FORMDATA:
            content_type = "multipart/form-data; boundary=AaB03x"
        elif content_type is WWWFORM:
            content_type = "application/x-www-form-urlencoded"
        headers = {"Content-Type": content_type}
    if not 'content-length' in headers:
        headers['Content-length'] = str(len(raw))
    headers['Host'] = 'Blah'
    return Body( Headers(headers)
               , StringIO(raw)
               , b""
                )


def test_body_is_instantiable():
    body = make_body("cheese=yes")
    actual = body.__class__.__name__
    assert actual == "Body"

def test_body_is_unparsed_for_empty_content_type():
    actual = make_body("cheese=yes", headers={})
    assert actual == {}

def test_body_gives_empty_dict_for_empty_body():
    actual = make_body("")
    assert actual == {}

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

from StringIO import StringIO

from aspen.http.request import Body, Headers

FORMDATA = object()
WWWFORM = object()

def make_body(raw, headers=None, content_type=WWWFORM):
    if headers is None:
        if content_type is FORMDATA:
            content_type = "multipart/form-data; boundary=AaB03x"
        elif content_type is WWWFORM:
            content_type = "application/x-www-form-urlencoded"
        headers = {"Content-Type": content_type}
    headers['Host'] = 'Blah'
    return Body( Headers(headers)
               , StringIO(raw)
               , ""
                )


def test_body_is_instantiable():
    body = make_body("cheese=yes")
    actual = body.__class__.__name__
    assert actual == "Body", actual

def test_body_is_unparsed_for_empty_content_type():
    actual = make_body("cheese=yes", headers={})
    assert actual == {}, actual

def test_body_gives_empty_dict_for_empty_body():
    actual = make_body("")
    assert actual == {}, actual

def test_body_barely_works():
    body = make_body("cheese=yes")
    actual = body['cheese']
    assert actual == "yes", actual


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
    assert actual == "file1.txt", actual

def test_simple_values_are_simple():
    body = make_body(UPLOAD, content_type=FORMDATA)
    actual = body['submit-name']
    assert actual == "Larry", actual

def test_params_doesnt_break_www_form():
    body = make_body("statement=foo"
                    , content_type="application/x-www-form-urlencoded; charset=UTF-8; cheese=yummy"
                     )
    actual = body['statement']
    assert actual == "foo", actual

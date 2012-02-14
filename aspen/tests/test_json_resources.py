from aspen.exceptions import LoadError
from aspen.tests import assert_raises
from aspen.tests.test_resources import check


def test_json_basically_works():
    expected = '{"Greetings": "program!"}'
    actual = check( "response.body = {'Greetings': 'program!'}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_cant_have_more_than_one_page_break():
    assert_raises(SyntaxError, check, "", filename="foo.json")

def test_json_defaults_to_application_json_for_static_json():
    expected = 'application/json'
    actual = check( '{"Greetings": "program!"}'
                  , filename="foo.json"
                  , body=False
                   ).headers.one('Content-Type')
    assert actual == expected, actual

def test_json_defaults_to_application_json_for_dynamic_json():
    expected = 'application/json'
    actual = check( "response.body = {'Greetings': 'program!'}"
                  , filename="foo.json"
                  , body=False
                   ).headers.one('Content-Type')
    assert actual == expected, actual

def test_json_content_type_is_configurable_for_static_json():
    aspenconf = '[aspen]\njson_content_type: floober/blah'
    expected = 'floober/blah'
    actual = check( '{"Greetings": "program!"}'
                  , filename="foo.json"
                  , body=False
                  , aspenconf=aspenconf
                   ).headers.one('Content-Type')
    assert actual == expected, actual

def test_json_content_type_is_configurable_for_dynamic_json():
    aspenconf = '[aspen]\njson_content_type: floober/blah'
    expected = 'floober/blah'
    actual = check( "response.body = {'Greetings': 'program!'}"
                  , filename="foo.json"
                  , body=False
                  , aspenconf=aspenconf
                   ).headers.one('Content-Type')
    assert actual == expected, actual

def test_json_handles_unicode():
    expected = '{"Greetings": "\u00b5"}'
    actual = check( "response.body = {'Greetings': unichr(181)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_doesnt_handle_non_ascii_bytestrings():
    assert_raises( UnicodeDecodeError
                 , check
                 , "response.body = {'Greetings': chr(181)}"
                 , filename="foo.json"
                  )

def test_json_handles_time():
    expected = '{"seen": "19:30:00"}'
    actual = check( "import datetime"
                  + ""
                  + "response.body = {'seen': datetime.time(19, 30)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_handles_date():
    expected = '{"created": "2011-05-09"}'
    actual = check( "import datetime"
                  + ""
                  + "response.body = {'created': datetime.date(2011, 5, 9)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_handles_datetime():
    expected = '{"timestamp": "2011-05-09T00:00:00"}'
    actual = check( "import datetime"
                  + ""
                  + "response.body = { 'timestamp'"
                  + "                : datetime.datetime(2011, 5, 9, 0, 0)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_handles_complex():
    expected = '{"complex": [1.0, 2.0]}'
    actual = check( "response.body = {'complex': complex(1,2)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_raises_TypeError_on_unknown_types():
    assert_raises( TypeError
                 , check
                 , "class Foo: passresponse.body = Foo()"
                 , filename="foo.json"
                  )



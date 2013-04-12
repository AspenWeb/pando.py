import StringIO

from aspen import json
from aspen.testing import assert_raises, check
from aspen.testing.fsfix import attach_teardown


def test_json_basically_works():
    expected = '{"Greetings": "program!"}'
    actual = check( "[----]\nresponse.body = {'Greetings': 'program!'}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_cant_have_more_than_one_page_break():
    assert_raises(SyntaxError, check, "[----]\n[----]\n", filename="foo.json")

def test_json_defaults_to_application_json_for_static_json():
    expected = 'application/json'
    actual = check( '{"Greetings": "program!"}'
                  , filename="foo.json"
                  , body=False
                   ).headers['Content-Type']
    assert actual == expected, actual

def test_json_defaults_to_application_json_for_dynamic_json():
    expected = 'application/json'
    actual = check( "[----]\nresponse.body = {'Greetings': 'program!'}"
                  , filename="foo.json"
                  , body=False
                   ).headers['Content-Type']
    assert actual == expected, actual

def test_json_content_type_is_configurable_for_static_json():
    configure_aspen_py = 'website.media_type_json = "floober/blah"'
    expected = 'floober/blah'
    actual = check( '{"Greetings": "program!"}'
                  , filename="foo.json"
                  , body=False
                  , configure_aspen_py=configure_aspen_py
                   ).headers['Content-Type']
    assert actual == expected, actual

def test_json_content_type_is_configurable_from_the_command_line():
    expected = 'floober/blah'
    actual = check( '{"Greetings": "program!"}'
                  , filename="foo.json"
                  , body=False
                  , argv=['--media_type_json=floober/blah']
                   ).headers['Content-Type']
    assert actual == expected, actual

def test_json_content_type_is_configurable_for_dynamic_json():
    configure_aspen_py = 'website.media_type_json = "floober/blah"'
    expected = 'floober/blah'
    actual = check( "[----]\nresponse.body = {'Greetings': 'program!'}"
                  , filename="foo.json"
                  , body=False
                  , configure_aspen_py=configure_aspen_py
                   ).headers['Content-Type']
    assert actual == expected, actual

def test_json_handles_unicode():
    expected = '{"Greetings": "\u00b5"}'
    actual = check( "[----]\nresponse.body = {'Greetings': unichr(181)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_doesnt_handle_non_ascii_bytestrings():
    assert_raises( UnicodeDecodeError
                 , check
                 , "[----]\nresponse.body = {'Greetings': chr(181)}"
                 , filename="foo.json"
                  )

def test_json_handles_time():
    expected = '{"seen": "19:30:00"}'
    actual = check( "import datetime\n"
                  + "[---------------]\n"
                  + "response.body = {'seen': datetime.time(19, 30)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_handles_date():
    expected = '{"created": "2011-05-09"}'
    actual = check( "import datetime\n"
                  + "[---------------]\n"
                  + "response.body = {'created': datetime.date(2011, 5, 9)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_handles_datetime():
    expected = '{"timestamp": "2011-05-09T00:00:00"}'
    actual = check( "import datetime\n"
                  + "[---------------]\n"
                  + "response.body = { 'timestamp'"
                  + "                : datetime.datetime(2011, 5, 9, 0, 0)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_handles_complex():
    expected = '{"complex": [1.0, 2.0]}'
    actual = check( "[----]\nresponse.body = {'complex': complex(1,2)}"
                  , filename="foo.json"
                   )
    assert actual == expected, actual

def test_json_raises_TypeError_on_unknown_types():
    assert_raises( TypeError
                 , check
                 , "class Foo: pass\n[----]\nresponse.body = Foo()"
                 , filename="foo.json"
                  )

def test_aspen_json_load_loads():
    fp = StringIO.StringIO()
    fp.write('{"cheese": "puffs"}')
    fp.seek(0)
    actual = json.load(fp)
    assert actual == {'cheese': 'puffs'}, actual

def test_aspen_json_dump_dumps():
    fp = StringIO.StringIO()
    json.dump({"cheese": "puffs"}, fp)
    fp.seek(0)
    actual = fp.read()
    assert actual == '{"cheese": "puffs"}', actual

def test_aspen_json_loads_loads():
    actual = json.loads('{"cheese": "puffs"}')
    assert actual == {'cheese': 'puffs'}, actual

def test_aspen_json_dumps_dumps():
    actual = json.dumps({'cheese': 'puffs'})
    assert actual == '{"cheese": "puffs"}', actual


# Teardown
# ========

attach_teardown(globals())

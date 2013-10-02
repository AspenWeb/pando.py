from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

from aspen.sockets.message import Message
from aspen.testing import teardown_function


def test_message_can_be_instantiated_from_bytes():
    expected = Message
    actual = Message.from_bytes('3:::').__class__
    assert actual is expected

def test_from_bytes_too_few_colons_raises_SyntaxError():
    exc = raises(SyntaxError, Message.from_bytes, '3:').value
    expected = "This message has too few colons: 3:."
    actual = exc.args[0]
    assert actual == expected

def test_from_bytes_data_part_is_optional():
    message = Message.from_bytes('3::')
    expected = ""
    actual = message.data
    assert actual == expected

def test_from_bytes_too_many_colons_and_the_extras_end_up_in_the_data():
    message = Message.from_bytes('3::::')
    expected = ":"
    actual = message.data
    assert actual == expected

def test_from_bytes_non_digit_type_raises_ValueError():
    exc = raises(ValueError, Message.from_bytes, 'foo:::').value
    expected = "The message type is not in 0..8: foo."
    actual = exc.args[0]
    assert actual == expected

def test_from_bytes_type_too_small_raises_ValueError():
    exc = raises(ValueError, Message.from_bytes, '-1:::').value
    expected = "The message type is not in 0..8: -1."
    actual = exc.args[0]
    assert actual == expected

def test_from_bytes_type_too_big_raises_ValueError():
    exc = raises(ValueError, Message.from_bytes, '9:::').value
    expected = "The message type is not in 0..8: 9."
    actual = exc.args[0]
    assert actual == expected

def test_from_bytes_type_lower_bound_instantiable():
    message = Message.from_bytes('0:::')
    expected = 0
    actual = message.type
    assert actual == expected

def test_from_bytes_type_upper_bound_instantiable():
    message = Message.from_bytes('8:::')
    expected = 8
    actual = message.type
    assert actual == expected

def test_id_passes_through():
    message = Message.from_bytes('3:deadbeef::')
    expected = 'deadbeef'
    actual = message.id
    assert actual == expected

def test_endpoint_passes_through():
    message = Message.from_bytes('3:deadbeef:/cheese.sock:')
    expected = '/cheese.sock'
    actual = message.endpoint
    assert actual == expected

def test_data_passes_through():
    message = Message.from_bytes('3:deadbeef:/cheese.sock:Greetings, program!')
    expected = 'Greetings, program!'
    actual = message.data
    assert actual == expected

def test_json_data_decoded():
    message = Message.from_bytes('''4:deadbeef:/cheese.sock:{
    "foo": "bar"
}''')
    expected = {"foo": "bar"}
    actual = message.data
    assert actual == expected

def test_json_roundtrip():
    bytes = '''4:deadbeef:/cheese.sock:{
    "foo": "bar"
}'''
    message = Message.from_bytes(bytes)
    expected = bytes
    actual = str(message)
    assert actual == expected

def test_event_data_decoded():
    message = Message.from_bytes('''5:::{
    "name": "bar", "args": []
}''')
    expected = {u'args': [], u'name': 'bar'}
    actual = message.data
    assert actual == expected

def test_event_data_without_name_raises_ValueError():
    exc = raises( ValueError
                            , Message.from_bytes
                            , '5:::{"noom": "bar", "args": []}'
                             ).value
    expected = "An event message must have a 'name' key."
    actual = exc.args[0]
    assert actual == expected

def test_event_data_without_args_raises_ValueError():
    exc = raises( ValueError
                            , Message.from_bytes
                            , '5:::{"name": "bar", "arrrrgs": []}'
                             ).value
    expected = "An event message must have an 'args' key."
    actual = exc.args[0]
    assert actual == expected

def test_event_data_with_reserved_name_raises_ValueError():
    exc = raises( ValueError
                       , Message.from_bytes
                       , '5:::{"name": "connect", "args": []}'
                        ).value
    expected = "That event name is reserved: connect."
    actual = exc.args[0]
    assert actual == expected




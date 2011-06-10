from aspen import Response
from aspen.tests import assert_raises
from aspen.tests.fsfix import attach_teardown


def test_response_is_a_wsgi_callable():
    response = Response(body="Greetings, program!")
    def start_response(status, headers):
        pass
    expected = ["Greetings, program!"]
    actual = response({}, start_response)
    assert actual == expected, actual

def test_response_want_template_defaults_to_True():
    response = Response(body="Greetings, program!")
    assert not response.bypass_templating


attach_teardown(globals())

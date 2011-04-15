from os.path import join
from textwrap import dedent

from aspen.http import Response
from aspen.simplates import handle, load_uncached 
from aspen.tests.fsfix import attach_teardown, mk


class StubRequest(object):
    def __init__(self, fs):
        """Takes a path under ./fsfix to a simplate.
        """
        self.root = join('.', 'fsfix')
        self.fs = join('.', 'fsfix', fs)
        self.namespace = {}
        class Foo:
            pass
        self.conf = Foo()
        self.conf.aspen = {}

def Simplate(fs):
    return load_uncached(StubRequest(fs))

def check(content):
    mk(('index.html', content))
    request = StubRequest('index.html')
    response = Response()
    handle(request, response)
    return response.body


# Tests
# =====

def test_barely_working():
    mk(('index.html', "Greetings, program!"))
    simplate = Simplate('index.html')
    actual = simplate[0]
    expected = 'text/html'
    assert actual == expected, actual

def test_handle_barely_working():
    mk(('index.html', "Greetings, program!"))
    request = StubRequest('index.html')
    response = Response()
    handle(request, response)
    actual = response.body
    expected = "Greetings, program!"
    assert actual == expected, actual

def test_simplate_pages_work():
    actual = check("foo = 'bar'Greetings, {{ foo }}!")
    expected = "Greetings, bar!"
    assert actual == expected, actual

def test_simplate_pages_work_with_caret_L():
    actual = check("foo = 'bar'^LGreetings, {{ foo }}!")
    expected = "Greetings, bar!"
    assert actual == expected, actual

def test_simplate_templating_set():
    actual = check(dedent("""
        foo = [1,2,3,4]
        nfoo = len(foo)

        
        {% set i = 0 %}
        {% for x in foo %}{% set i += 1 %}{{ x }}{% if i < nfoo %}, {% end %}{% end %}
            """)).strip()
    expected = "1, 2, 3, 4"
    assert actual == expected, actual

def test_simplates_dont_leak_whitespace():
    """This aims to resolve https://github.com/whit537/aspen/issues/8.

    It is especially weird with JSON output, which we test below. When
    you return [1,2,3,4] that's what you want in the HTTP response
    body.

    """
    actual = check(dedent("""
        
        json_list = [1,2,3,4]
        
        {{repr(json_list)}}
        """))
    expected = "[1, 2, 3, 4]\n"
    assert actual == expected, repr(actual)

attach_teardown(globals())

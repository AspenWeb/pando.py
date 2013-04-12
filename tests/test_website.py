import os

from aspen.testing import handle, StubRequest
from aspen.testing.fsfix import attach_teardown, FSFIX, mk
from aspen.website import Website


# Tests
# =====

def test_basic():
    website = Website([])
    expected = os.getcwd()
    actual = website.www_root
    assert actual == expected, actual

def test_normal_response_is_returned():
    mk(('index.html', "Greetings, program!"))
    expected = '\r\n'.join("""\
HTTP/1.1
Content-Type: text/html

Greetings, program!
""".splitlines())
    actual = handle()._to_http('1.1')
    assert actual == expected, actual

def test_fatal_error_response_is_returned():
    mk(('index.html', "raise heck\n[----]\n"))
    expected = 500
    actual = handle().code
    assert actual == expected, actual

def test_nice_error_response_is_returned():
    mk(('index.html', "from aspen import Response\n[----]\nraise Response(500)\n[----]\n"))
    expected = 500
    actual = handle().code
    assert actual == expected, actual

def test_nice_error_response_is_returned_for_404():
    mk(('index.html', "from aspen import Response\n[----]\nraise Response(404)\n[----]\n"))
    expected = 404
    actual = handle().code
    assert actual == expected, actual

def test_autoindex_response_is_404_by_default():
    mk(('README', "Greetings, program!"))
    expected = 404
    actual = handle().code
    assert actual == expected, actual

def test_autoindex_response_is_returned():
    mk(('README', "Greetings, program!"))
    expected = True
    actual = 'README' in handle('/', '--list_directories=TrUe').body
    assert actual == expected, actual

def test_resources_can_import_from_dot_aspen():
    mk( '.aspen'
      , ('.aspen/foo.py', 'bar = "baz"')
      , ('index.html', "import foo\n[----]\nGreetings, {{ foo.bar }}!")
       )
    expected = "Greetings, baz!"
    project_root = os.path.join(FSFIX, '.aspen')
    actual = handle('/', '--project_root='+project_root).body
    assert actual == expected, actual


def test_double_failure_still_sets_response_dot_request():
    mk( '.aspen'
      , ('.aspen/foo.py', """
def bar(response):
    response.request
""")
      , ( '.aspen/configure-aspen.py'
        , 'import foo\nwebsite.hooks.outbound.append(foo.bar)'
         )
      , ('index.html', "raise heck\n[----]\n")
       )

    # Intentionally break the website object so as to trigger a double failure.
    project_root = os.path.join(FSFIX, '.aspen')
    website = Website(['--www_root='+FSFIX, '--project_root='+project_root])
    del website.renderer_factories

    response = website.handle_safely(StubRequest())

    expected = 500
    actual = response.code
    assert actual == expected, actual


def test_website_doesnt_clobber_outbound():
    mk( ( '.aspen/configure-aspen.py'
        , 'import random\nwebsite.hooks.outbound.append(random.choice)'
         )
       )

    project_root = os.path.join(FSFIX, '.aspen')
    website = Website(['--www_root='+FSFIX, '--project_root='+project_root])

    expected = 2
    actual = len(website.hooks.outbound)
    assert actual == expected, actual



attach_teardown(globals())

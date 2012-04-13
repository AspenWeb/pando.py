from os.path import join
from textwrap import dedent

from aspen import Response
from aspen.configuration import Configurable
from aspen.exceptions import LoadError
from aspen.testing import assert_raises, check
from aspen.testing.fsfix import attach_teardown
from aspen._tornado.template import Template, Loader



# Tests
# =====

def test_barely_working():
    response = check("Greetings, program!", 'index.html', False)
   
    expected = 'text/html'
    actual = response.headers['Content-Type']
    assert actual == expected, actual

def test_resource_pages_work():
    expected = "Greetings, bar!"
    actual = check("foo = 'bar'Greetings, {{ foo }}!")
    assert actual == expected, actual

def test_resource_pages_work_with_caret_L():
    expected = "Greetings, bar!"
    actual = check("foo = 'bar'^LGreetings, {{ foo }}!")
    assert actual == expected, actual

def test_resource_templating_set():
    expected = "1, 2, 3, 4"
    actual = check(dedent("""
        foo = [1,2,3,4]
        nfoo = len(foo)

        
        {% set i = 0 %}
        {% for x in foo %}{% set i += 1 %}{{ x }}{% if i < nfoo %}, {% end %}{% end %}
            """)).strip()
    assert actual == expected, actual

def test_tornado_utf8_works_without_whitespace():
    expected = unichr(1758).encode('utf8')
    actual = Template(u"{{ text }}").generate(text=unichr(1758))
    assert actual == expected, actual

def test_tornado_utf8_breaks_with_whitespace():
    template = Template(u" {{ text }}")
    assert_raises(UnicodeDecodeError, template.generate, text=unichr(1758))

def test_utf8():
    expected = unichr(1758).encode('utf8')
    actual = check("""
"empty first page"
^L
text = unichr(1758)
^L
{{ text }}
    """).strip()
    assert actual == expected, actual

def test_resources_dont_leak_whitespace():
    """This aims to resolve https://github.com/whit537/aspen/issues/8.
    """
    actual = check(dedent("""
        
        foo = [1,2,3,4]
        {{repr(foo)}}"""))
    expected = "[1, 2, 3, 4]"
    assert actual == expected, repr(actual)


# Unicode example in the /templating/ doc.
# ========================================
# See also: https://github.com/whit537/aspen/issues/10

eg = """\
latinate = chr(181).decode('latin1')
response.headers['Content-Type'] = 'text/plain; charset=latin1'
^L
{{ latinate.encode('latin1') }}"""

def test_content_type_is_right_in_template_doc_unicode_example():
    response = check(eg, body=False)
    expected = "text/plain; charset=latin1"
    actual = response.headers['Content-Type']
    assert actual == expected, actual

def test_body_is_right_in_template_doc_unicode_example():
    expected = chr(181)
    actual = check(eg).strip()
    assert actual == expected, actual


# raise Response
# ==============

def test_raise_response_works():
    expected = 404
    response = assert_raises( Response
                            , check
                            , "from aspen import Response; raise Response(404)"
                             )
    actual = response.code
    assert actual == expected, actual


def test_website_is_in_context():
    expected = "It worked."
    actual = check("""\
assert website.__class__.__name__ == 'Configurable', website


It worked.""")
    assert actual == expected, actual

def test_unknown_mimetype_yields_default_mimetype():
    response = check( "Greetings, program!"
                    , body=False
                    , filename="foo.flugbaggity"
                     )
    expected = "text/plain"
    actual = response.headers['Content-Type']
    assert actual == expected, actual

def test_templating_skipped_without_script():
    response = Response()
    expected = "{{ foo }}"
    actual = check("{{ foo }}", response=response)
    assert actual == expected, actual


# Teardown
# ========

attach_teardown(globals())

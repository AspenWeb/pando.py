"""Implement server-side includes as implemented in Apache's mod_include.

This module is currently very incomplete:

    - elements: only 'include'
    - variable substitutions: none
    - flow control: none
    - options: none (should go in aspen.conf [ssi] section)

"""
import os
import re

if __name__ == '__main__':
    import aspen
    aspen.configure()

from aspen.utils import WSGIFilter
from aspen.handlers import static

element = re.compile(r"(<!--#(\S*)\s+(.*?)\s+-->)", re.DOTALL)
WHITESPACE = ' \n\r\t'


class ServerSideIncludeFilter(WSGIFilter):
    """Middleware that filters the body as a (partial) server-side include.
    """

    def filter(self, environ, headers, data):
        elements = element.findall(data)
        for whole, command, raw_attrs in elements:
            meth = getattr(self, 'do_'+command, )
            if meth is None:
                raise NotImplementedError("Unknown SSI command '%s'" % command)
            replacement = meth(environ, headers, **self.parse_attrs(raw_attrs))
            data = data.replace(whole, replacement)

        _headers = []
        for k,v in headers:
            if k.lower() != 'content-length':
                _headers.append((k,v))
        headers[:] = _headers

        return data


    def parse_attrs(self, raw):
        """Given a raw string, return an attrs dict per Apache mod_include:

          http://httpd.apache.org/docs/2.0/mod/mod_include.html#elements

        """

        attrs = dict()
        attr = []
        val = []
        quote = Q = ''

        for c in raw:
            if isinstance(attr, list):      # gathering attribute
                if (attr == []) and c in WHITESPACE:
                    continue
                if c == '=':
                    attr = ''.join(attr)
                    val = []
                else:
                    attr.append(c)
            elif isinstance(val, list):     # gathering value; deal w/ quoting
                if val == []:
                    if c in ('"', "'", '`'):
                        quote = Q = c
                    else:
                        val.append(c)
                elif (Q and (c == Q)) or (not Q and (c in WHITESPACE)):
                    val = ''.join(val)
                    attrs[attr] = val and val or None
                    attr = []
                    val = []
                    quote = Q = ''
                else:
                    val.append(c)


        # Finalize
        # ========
        # Make sure quote was closed; finish the last loop; 'file' is a
        # reserved word.

        if quote != '':
            raise StandardError("Unclosed quote in <%s>" % raw)
        elif attr:
            val = ''.join(val)
            attrs[''.join(attr)] = val and val or None

        if 'file' in attrs:
            attrs['filepath'] = attrs['file']
            del attrs['file']

        return attrs


    # Elements
    # ========

    def do_config(self, environ, headers, errmsg=None, sizefmt=None, timefmt=None):
        """http://httpd.apache.org/docs/2.0/mod/mod_include.html#element.config
        """
        raise NotImplementedError


    def do_echo(self, environ, headers, var, encoding=None):
        """http://httpd.apache.org/docs/2.0/mod/mod_include.html#element.echo
        """
        raise NotImplementedError


    def do_exec(self, environ, headers, var, encoding=None):
        """http://httpd.apache.org/docs/2.0/mod/mod_include.html#element.exec
        """
        raise NotImplementedError


    def do_fsize(self, environ, headers, filepath=None, virtual=None):
        """http://httpd.apache.org/docs/2.0/mod/mod_include.html#element.fsize
        """
        raise NotImplementedError


    def do_flastmod(self, environ, headers, filepath=None, virtual=None):
        """http://httpd.apache.org/docs/2.0/mod/mod_include.html#element.flastmod
        """
        raise NotImplementedError


    def do_include(self, environ, headers, filepath=None, virtual=None):
        """http://httpd.apache.org/docs/2.0/mod/mod_include.html#element.include
        """
        both = (filepath, virtual)
        if None not in both:
            raise TypeError("Can't set both 'file' and 'virtual'.")
        elif both == (None, None):
            raise TypeError("Must set either 'file' or 'virtual'.")
        if filepath:
            err = ValueError("The 'file' setting is not within scope.")
            assert '..'+os.sep not in filepath, err
            assert not filepath.startswith(os.sep), err
            parent = os.path.dirname(environ['PATH_TRANSLATED'])
            out = open(os.path.join(parent, filepath)).read()
        else:
            assert virtual is not None # sanity check
            raise NotImplementedError
        return out


    def do_printenv(self, environ, headers):
        """http://httpd.apache.org/docs/2.0/mod/mod_include.html#element.printenv
        """
        raise NotImplementedError


    def do_set(self, environ, headers, var, value):
        """http://httpd.apache.org/docs/2.0/mod/mod_include.html#element.set
        """
        raise NotImplementedError


    # Flow Control
    # ============
    # http://httpd.apache.org/docs/2.0/mod/mod_include.html#flowctrl

    def do_if(self, environ, headers, expr):
        """
        """
        raise NotImplementedError


    def do_elif(self, environ, headers, expr):
        """
        """
        raise NotImplementedError


    def do_else(self, environ, headers, expr):
        """
        """
        raise NotImplementedError


    def do_endif(self, environ, headers, expr):
        """
        """
        raise NotImplementedError


wsgi = ServerSideIncludeFilter(static.wsgi) # wire this in __/etc/handlers.conf


if __name__ == '__main__':

    from aspen.tests import assert_raises


    # element
    # =======

    expected = [('<!--#foo bar baz -->', 'foo', 'bar baz')]
    actual = element.findall("Hey There! <!--#foo bar baz --> Blam!")
    assert actual == expected, actual

    expected = [ ('<!--#foo bar baz -->', 'foo', 'bar baz')
               , ('<!--#bar buz blim -->', 'bar', 'buz blim')
                ]
    actual = element.findall("""\

        Hey There!

        <!--#foo bar baz -->
        <!--#bar buz blim -->

        Blam!

    """)
    assert actual == expected, actual

    expected = [ ( '<!--#foo bar\n        baz -->'
                 , 'foo', 'bar\n        baz'
                  )
               , ( '<!--#bar buz\n\n\n\n        blim -->'
                 , 'bar', 'buz\n\n\n\n        blim'
                  )
                ]
    actual = element.findall("""\

        Hey There!

        <!--#foo bar
        baz --><!--#bar buz



        blim -->

        Blam!

    """)
    assert actual == expected, actual


    # parse
    # =====

    func = ServerSideIncludeFilter(None).parse_attrs

    expected = [('foo', 'bar')]
    actual = sorted(func('foo=bar').items())
    assert actual == expected, actual

    expected = [('foo', '')]
    actual = sorted(func('foo').items())
    assert actual == expected, actual

    expected = [('foo', '')]
    actual = sorted(func('foo=').items())
    assert actual == expected, actual

    expected = [('foo', 'bar')]
    actual = sorted(func('foo="bar"').items())
    assert actual == expected, actual

    expected = [('foo', 'bar')]
    actual = sorted(func("foo='bar'").items())
    assert actual == expected, actual

    expected = [('foo', 'bar')]
    actual = sorted(func('foo=`bar`').items())
    assert actual == expected, actual

    expected = 'Unclosed quote in <foo="bar`>'
    actual = assert_raises( StandardError
                          , func
                          , 'foo="bar`'
                           ).args[0]
    assert actual == expected, actual

    expected = [('baz', 'buz'), ('foo', 'bar')]
    actual = sorted(func('foo=bar baz=buz').items())
    assert actual == expected, actual

    expected = [('baz', 'buz=boooz'), ('foo', 'bar')]
    actual = sorted(func('foo=bar baz=buz=boooz').items())
    assert actual == expected, actual

    expected = [('baz', 'buz=boooz'), ('foo', 'bar')]
    actual = sorted(func('foo=bar baz=buz=boooz  ').items())
    assert actual == expected, actual

    expected = [('baz', 'buz boooz'), ('foo', 'bar')]
    actual = sorted(func('foo=bar baz="buz boooz"').items())
    assert actual == expected, actual

    expected = [('baz', 'buz boooz'), ('foo', 'bar')]
    actual = sorted(func("foo=bar baz='buz boooz'").items())
    assert actual == expected, actual

    expected = [('baz', 'buz boooz'), ('foo', 'bar')]
    actual = sorted(func('foo=bar baz=`buz boooz`').items())
    assert actual == expected, actual


    # We win!
    # =======

    print "tests pass"

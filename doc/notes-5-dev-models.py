========================================
    Intro
========================================

Hey gang! My name's Chad Whitacre, and in this screencast I'm going to talk
about Aspen. Aspen is a Python web server that I just released. It's all about
organizing your WSGI applications into an integrated website, and in this
screencast I'm going to show you proofs of concept for five different
development models that Aspen supports. They are:

    1. Static HTML
    2. CGI-style
    3. PHP-style
    4. RoR-style
    5. Zope-style

I'll explain what I mean by each of these terms as we go along, and again, these
are all just proofs of concept. It's going to take a little more work to really
flesh these patterns out with Aspen.


========================================
    1. Static
========================================

One of my goals with Aspen is to be able to use the same web server from initial
concept through development and into production. So whether you're doing
wireframes, temporary pages, tiny sites, or boilerplate pages on a larger site,
there are definitely times when you just want to serve some stupid simple HTML,
with maybe some CSS, images, and JavaScript thrown in to boot.

Aspen takes this use-case seriously. Just create a directory, stick your files
in it, and Aspen will happily serve away.


========================================
    2. CGI-style
========================================
.py extension
environ mapping
start_response


========================================
    3. PHP-style
========================================

PHP-style web development is the model where your URLs map literally to
templates on the filesystem, which are somehow processed to generate the HTTP
response. Ian Bicking has got a really cool hack to wrap a PHP FastCGI process
within a Python WSGI callable, and I'm going to wire that up here as an Aspen
handler to process all *.php files.

First, you need to have php installed, with FastCGI support. This probably isn't
in your packaging system, so that means recompiling from source. Grab a tarball
from www.php.net, and do:

    $ ./configure --enable-fastcgi
    $ make
    $ make install dance


You can verify that it is installed correctly with:

    $ ~/php/bin/php -v
    PHP 4.4.4 (cgi-fcgi) (built: Nov 20 2006 15:38:26)
    Copyright (c) 1997-2006 The PHP Group
    Zend Engine v1.3.0, Copyright (c) 1998-2004 Zend Technologies


Once php is installed, wiring it up to Aspen is fairly simple:

    $ cd __/lib/python2.4
    $ svn export http://svn.pythonpaste.org/Paste/wphp/trunk/wphp
    $ vi phplease.py

        import wphp

        class PHPlease(wphp.PHPApp):
            def __init__(self, website):
                wphp.PHPApp.__init__(self, base_dir=website.paths.root)

    $ cd ../../etc
    $ vi handlers.conf

    Add all of the other handlers, plus:

    [phplease]
    fnmatch *.php



========================================
    4. RoR-style
========================================

By Ruby-on-Rails-style web development, I mean full-stack web frameworks. The
leading such option in Python is Django, so I'm going to show you how to plug a
Django application into an Aspen website. As a proof of concept this is pretty
easy, because Django comes bundled with a WSGI adapter.

    $ cd __/src
    $ fetch <django.tgz>
    $ tar zxf <django.tgz>
    $ cd <django>
    $ python setup.py install --prefix=../../
    $ cd ../../
    $ bin/django-admin.py startproject hotclub
    $ vi etc/apps.conf
    /hotclub   django.core.handlers.wsgi:WSGIHandler


========================================
    5. Zope-style
========================================
any file becomes a rich content object
great for little one-off apps
    use OS tools for create/update/delete





========================================
    Conclusion
========================================

So that's about it. Five different development models that you can mix and match
when building websites with Aspen. If Aspen looks like it might help you out in
your web development, then you can find out more at zetadev.com/software/aspen.
Thanks!

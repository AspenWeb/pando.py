"""Three-part resources.

thin wedge to allow a simplate to handle all requests for at or below a given
directory: nope, use middleware for that to rewrite URLs and pass through

========================================
    User's POV
========================================

1. install framework

    $ easy_install django


2. configure framework

    $ django-admin.py startproject foo
    $ vi foo/settings.py


3. wire framework in aspen.conf

    [django]
    settings_module = foo.settings


4. wire up handlers.conf

    [aspen.handlers.simplates:django
    fnmatch *.html


5. GGG!


========================================
    Request Processing
========================================

request comes in, matches simplates:<framework> in handlers.conf
control passes to aspen.handlers.simplates:<framework>
simplates:<framework> loads the simplate from a cache
    cache can be global to Aspen handlers (static only other?)
    cache is tunable by mem-size, max obj size
    cache invalidates on tunables + resource modtime
    cache is thread-safe
    cache builds simplate
        import section is always built and run the same
        script section is always built the same, but is run differently
        template section needs to be built differently for each type (but buffet?)
simplates:wsgi runs the script
    namespace population is framework-specific
    raise SystemExit => stop script, proceed to template
    raise SystemExit(response) => stop script, skip template, return response
        response obj is framework-specific
    @@: allow multiple frameworks in one simplate?
simplates:wsgi renders the template
    uses buffet's render API?
        need a Buffet wrapper for Django and ZPT, eh?
    building contexts will differ by framework
simplates:wsgi converts response/rendered template to WSGI return val



========================================
    SIMPLATE ALGORITHM
========================================
1. check that we are processing a file
2. call load_simplate
3. add anything special to namespace
4. run the script
5. get the response
6. render the template
7. return


"""
import os
import traceback


# Basic simplates are always available.
# =====================================

from stdlib import wsgi as stdlib # relative for separability


# Framework simplates depend on the framework being installed.
# ============================================================

def stub(framework, problem):
    """Given a framework string and an ImportError, return a stub WSGI callable.
    """
    def stub(environ, start_response):
        msg = "We couldn't import the '%s' framework for this reason: " % framework
        msg = os.linesep.join([msg, problem])
        raise ImportError(msg)
    return stub


# @@: for loop here w/ more frameworks
excs = (ImportError,)

# Django
# ======

try:
    # django may be available but we don't want to use it here
    from django.core.exceptions import ImproperlyConfigured
    excs = (EnvironmentError, ImportError, ImproperlyConfigured)
except ImportError:
    pass

try:
    from django_ import wsgi as django
except excs:
    problem = traceback.format_exc()
    django = stub('django', problem)


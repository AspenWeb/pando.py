"""
Provide a WSGI callable.

(It could be nice if this was at ``pando:wsgi`` instead of ``pando.wsgi:website``,
but then Website would be instantiated every time you import the ``pando`` module.
Here, it's only instantiated when you pass this to a WSGI server like gunicorn,
spawning, etc.)

"""

from .website import Website

#: This is the WSGI callable, an instance of :class:`.Website`.
website = Website()

#: Alias of ``website``. A number of WSGI servers look for this name by default,
#: for example running ``gunicorn pando.wsgi`` works.
application = website

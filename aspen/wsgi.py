"""Provide a WSGI callable.

It would be a little nicer if this was at aspen:wsgi instead of
aspen.wsgi:website, but then Website would be instantiated even if we don't
want it to be. Here, it's only instantiated when someone passes this to
gunicorn, spawning, etc.

"""
from aspen.website import Website

website = Website([])

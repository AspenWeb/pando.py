"""
:mod:`website`
==============
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from copy import copy
import datetime
import os
import string

from aspen.request_processor import RequestProcessor
from aspen.simplates.simplate import Simplate
from state_chain import StateChain

from . import body_parsers
from .http.response import Response
from .urlparse import quote
from .utils import maybe_encode, to_rfc822, utc
from .exceptions import BadLocation

# 2006-11-17 was the first release of pando - v0.3
THE_PAST = to_rfc822(datetime.datetime(2006, 11, 17, tzinfo=utc))


PANDO_DIR = os.path.dirname(os.path.abspath(__file__))


class Website(object):
    """Represent a website.

    This object holds configuration information, and how to handle HTTP
    requests (per WSGI). It is available to user-developers inside of their
    simplates and state chain functions.

    :arg kwargs: configuration values. The available options and their default
                 values are described in :class:`pando.website.DefaultConfiguration`
                 and :class:`aspen.request_processor.DefaultConfiguration`.

    """

    def __init__(self, **kwargs):
        #: An Aspen :class:`~aspen.request_processor.RequestProcessor` instance.
        self.request_processor = RequestProcessor(**kwargs)

        pando_resources_dir = os.path.join(PANDO_DIR, 'www')
        self.request_processor.resource_directories.append(pando_resources_dir)

        pando_chain = StateChain.from_dotted_name('pando.state_chain')
        pando_chain.functions = [
            getattr(f, 'placeholder_for', f) for f in pando_chain.functions
        ]
        #: The chain of functions used to process an HTTP request, imported from
        #: :mod:`pando.state_chain`.
        self.state_chain = pando_chain

        # configure from defaults and kwargs
        defaults = [(k, v) for k, v in DefaultConfiguration.__dict__.items() if k[0] != '_']
        for name, default in sorted(defaults):
            if name in kwargs:
                self.__dict__[name] = kwargs[name]
            else:
                self.__dict__[name] = copy(default)

        # add ourself to the initial context of simplates
        Simplate.defaults.initial_context['website'] = self

        # load bodyparsers
        #: Mapping of content types to parsing functions.
        self.body_parsers = {
            "application/x-www-form-urlencoded": body_parsers.formdata,
            "multipart/form-data": body_parsers.formdata,
            self.request_processor.media_type_json: body_parsers.jsondata
        }

    def __call__(self, environ, start_response):
        """Alias of :meth:`wsgi_app`.
        """
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        """WSGI interface.

        Wrap this method (instead of the website object itself) when you want
        to use WSGI middleware::

            website = Website()
            website.wsgi_app = WSGIMiddleware(website.wsgi_app)

        """
        response = self.respond(environ)['response']
        return response.to_wsgi(environ, start_response, self.request_processor.encode_output_as)

    def respond(self, environ, raise_immediately=None, return_after=None):
        """Given a WSGI environ, return a state dict.
        """
        return self.state_chain.run(
            website=self,
            environ=environ,
            _raise_immediately=raise_immediately,
            _return_after=return_after,
        )

    def redirect(self, location, code=None, permanent=False, base_url=None, response=None):
        """Raise a redirect Response.

        If code is None then it will be set to 301 (Moved Permanently) if
        permanent is True and 302 (Found) if it is False. If url doesn't start
        with base_url (defaulting to self.base_url), then we prefix it with
        base_url before redirecting. This is a protection against open
        redirects. If you wish to use a relative path or full URL as location,
        then base_url must be the empty string; if it's not, we raise
        BadLocation. If you provide your own response we will set .code and
        .headers['Location'] on it.

        """
        response = response if response else Response()
        response.code = code if code else (301 if permanent else 302)
        base_url = base_url if base_url is not None else self.base_url
        location = quote(location, string.punctuation)
        if not location.startswith(base_url):
            newloc = base_url + location
            if not location.startswith('/'):
                raise BadLocation(newloc)
            location = newloc
        response.headers[b'Location'] = maybe_encode(location)
        raise response


    # Base URL Canonicalization
    # =========================

    def _extract_scheme(self, request):
        return request.headers.get(b'X-Forwarded-Proto', b'http')  # Heroku

    def _extract_host(self, request):
        return request.headers[b'Host']  # will 400 if missing

    _canonicalize_base_url_code = 302

    def canonicalize_base_url(self, request):
        """Enforces a base_url such as http://localhost:8080 (no path part).
        """
        if not self.base_url:
            return

        scheme = self._extract_scheme(request).decode('ascii', 'backslashreplace')
        host = self._extract_host(request).decode('ascii', 'backslashreplace')

        actual = scheme + "://" + host

        if actual != self.base_url:
            url = self.base_url
            if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
                # Redirect to a particular path for idempotent methods.
                url += request.line.uri.path.decoded
                if request.line.uri.querystring:
                    url += '?' + request.line.uri.querystring.decoded
            else:
                # For non-idempotent methods, redirect to homepage.
                url += '/'
            self.redirect(url, code=self._canonicalize_base_url_code)


    # File Resolution
    # ===============

    def find_ours(self, filename):
        """Given a ``filename``, return the filepath to pando's internal version
        of that filename.

        No existence checking is done, this just abstracts away the ``__file__``
        reference nastiness.
        """
        return os.path.join(PANDO_DIR, 'www', filename)

    def ours_or_theirs(self, filename):
        """Given a filename, return a filepath or ``None``.

        It looks for the file in :attr:`self.project_root`, then in Pando's
        default files directory. ``None`` is returned if the file is not found
        in either location.
        """
        if self.project_root is not None:
            theirs = os.path.join(self.project_root, filename)
            if os.path.isfile(theirs):
                return theirs

        ours = self.find_ours(filename)
        if os.path.isfile(ours):
            return ours

        return None


    # Backward compatibility
    # ======================

    @property
    def default_renderers_by_media_type(self):
        "Reference to :obj:`Simplate.default_renderers_by_media_type`, for backward compatibility."
        return Simplate.default_renderers_by_media_type

    @property
    def project_root(self):
        "Reference to :obj:`self.request_processor.project_root`, for backward compatibility."
        return self.request_processor.project_root

    @property
    def renderer_factories(self):
        "Reference to :obj:`Simplate.renderer_factories`, for backward compatibility."
        return Simplate.renderer_factories

    @property
    def www_root(self):
        "Reference to :obj:`self.request_processor.www_root`, for backward compatibility."
        return self.request_processor.www_root


class DefaultConfiguration(object):
    """Default configuration of :class:`Website` objects.
    """

    base_url = ''
    """
    The website's base URL (scheme and host only, no path). If specified, then
    requests for URLs that don't match it are automatically redirected. For
    example, if ``base_url`` is ``https://example.net``, then a request for
    ``http://www.example.net/foo`` is redirected to ``https://example.net/foo``.
    """

    colorize_tracebacks = True
    "Use the Pygments package to prettify tracebacks with syntax highlighting."

    list_directories = False
    "List the contents of directories that don't have a custom index."

    show_tracebacks = False
    "Show Python tracebacks in error responses."

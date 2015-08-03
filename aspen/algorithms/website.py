"""
aspen.algorithms.website
~~~~~~~~~~~~~~~~~~~~~~~~

These functions comprise the request processing functionality of Aspen.

The order of functions in this module defines Aspen algorithm for request
processing. The actual parsing is done by Algorithm.from_dotted_name():

http://algorithm-py.readthedocs.org/en/1.0.0/#algorithm.Algorithm.from_dotted_name

Dependencies are injected as
specified in each function definition. Each function should return None, or a
dictionary that will be used to update the algorithm state in the calling
routine.

The naming convention we've adopted for the functions in this file is:

    verb_object_preposition_object-of-preposition

For example:

    parse_environ_into_request

All four parts are a single word each (there are exactly three underscores in
each function name). This convention is intended to make function names easy to
understand and remember.

It's important that function names remain relatively stable over time, as
downstream applications are expected to insert their own functions into this
algorithm based on the names of our functions here. A change in function names
or ordering here would constitute a backwards-incompatible change.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import traceback

from first import first as _first

from .. import log as _log
from .. import log_dammit as _log_dammit
from .. import dispatcher, resources, body_parsers, typecasting
from ..http.request import Request
from ..http.response import Response
from ..dispatcher import DispatchResult, DispatchStatus
from ..simplates import SimplateException

def parse_environ_into_request(environ):
    return {'request': Request.from_wsgi(environ)}


def parse_body_into_request(request, website):
    request._parse_body = lambda _: body_parsers.parse_body( request.raw_body
                                                           , request.headers
                                                           , website.body_parsers
                                                            )


def raise_200_for_OPTIONS(request):
    """A hook to return 200 to an 'OPTIONS *' request"""
    if request.line.method == "OPTIONS" and request.line.uri == "*":
        raise Response(200)


def redirect_to_base_url(website, request):
    website.canonicalize_base_url(request)


def dispatch_request_to_filesystem(website, request):

    if website.list_directories:
        directory_default = website.ours_or_theirs('autoindex.html.spt')
        assert directory_default is not None  # sanity check
    else:
        directory_default = None

    result = dispatcher.dispatch( indices               = website.indices
                                , media_type_default    = website.media_type_default
                                , pathparts             = request.line.uri.path.parts
                                , uripath               = request.line.uri.path.raw
                                , querystring           = request.line.uri.querystring.raw
                                , startdir              = website.www_root
                                , directory_default     = directory_default
                                , favicon_default       = website.find_ours('favicon.ico')
                                , redirect              = website.redirect
                                 )

    for k, v in result.wildcards.iteritems():
        request.line.uri.path[k] = v
    return {'dispatch_result': result}


def apply_typecasters_to_path(website, request, state):
    typecasting.apply_typecasters( website.typecasters
                                 , request.line.uri.path
                                 , state
                                  )


def get_resource_for_request(website, dispatch_result):
    return {'resource': resources.get(website, dispatch_result.match)}


def extract_accept_from_request(request):
    return {'accept_header': request.headers.get('accept')}


def get_response_for_resource(state, website, resource=None):
    if resource is not None:
        state.setdefault('response', Response(charset=website.charset_dynamic))
        return {'response': resource.respond(state)}


def get_response_for_exception(website, exception):
    tb = traceback.format_exc()
    if isinstance(exception, Response):
        response = exception
    else:
        response = Response(500)
        if website.show_tracebacks:
            response.body = tb
    return {'response': response, 'traceback': tb, 'exception': None}


def log_traceback_for_5xx(response, traceback=None):
    if response.code >= 500:
        if traceback:
            _log_dammit(traceback)
        else:
            _log_dammit(response.body)
    return {'traceback': None}


def delegate_error_to_simplate(website, state, response, request=None, resource=None):
    if request is None:
        return  # early parsing must've failed
    if response.code < 400:
        return

    code = str(response.code)
    possibles = [code + ".spt", "error.spt"]
    fspath = _first(website.ours_or_theirs(errpage) for errpage in possibles)

    if fspath is not None:
        request.original_resource = resource
        if resource is not None and resource.default_media_type != website.media_type_default:
            # Try to return an error that matches the type of the original resource.
            state['accept_header'] = resource.default_media_type + ', text/plain; q=0.1'
        resource = resources.get(website, fspath)
        state['dispatch_result'] = DispatchResult( DispatchStatus.okay
                                                 , fspath
                                                 , {}
                                                 , 'Found.'
                                                 , {}
                                                 , True
                                                  )
        try:
            response = resource.respond(state)
        except Response as response:
            if response.code != 406:
                raise

    return {'response': response, 'exception': None}


def log_traceback_for_exception(website, exception):
    tb = traceback.format_exc()
    _log_dammit(tb)
    response = Response(500)
    if website.show_tracebacks:
        response.body = tb
    return {'response': response, 'exception': None}


def log_result_of_request(website, request=None, dispatch_result=None, response=None):
    """Log access. With our own format (not Apache's).
    """

    if website.logging_threshold > 0: # short-circuit
        return


    # What was the URL path translated to?
    # ====================================

    if request is None:
        msg = "(no request available)"
    else:
        fspath = getattr(dispatch_result, 'match', '')
        if fspath.startswith(website.www_root):
            fspath = fspath[len(website.www_root):]
            if fspath:
                fspath = '.' + fspath
        else:
            fspath = '...' + fspath[-21:]
        msg = "%-24s %s" % (request.line.uri.path.raw, fspath)


    # Where was response raised from?
    # ===============================

    if response is None:
        response = "(no response available)"
    else:
        filename, linenum = response.whence_raised()
        if filename is not None:
            response = "%s (%s:%d)" % (response, filename, linenum)
        else:
            response = str(response)

    # Log it.
    # =======

    _log("%-36s %s" % (response, msg))

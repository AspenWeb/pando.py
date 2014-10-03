"""
aspen.algorithms.website
~~~~~~~~~~~~~~~~~~~~~~~~

These functions comprise the request processing functionality of Aspen.

Per the algorithm.py module, the functions defined in this present module are
executed in the order they're defined here, with dependencies injected as
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

import aspen
from aspen import dispatcher, resources, body_parsers
from aspen.http.request import Request
from aspen.http.response import Response
from aspen import typecasting
from first import first as _first
from aspen.dispatcher import DispatchResult, DispatchStatus


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
                                 )

    for k, v in result.wildcards.iteritems():
        request.line.uri.path[k] = v
    return {'dispatch_result': result}


def apply_typecasters_to_path(website, request):
    typecasting.apply_typecasters(website.typecasters, request.line.uri.path)


def get_resource_for_request(website, request, dispatch_result):
    return {'resource': resources.get(website, request, dispatch_result.match)}


def get_response_for_resource(request, dispatch_result, resource=None):
    if resource is not None:
        return {'response': resource.respond(request, dispatch_result)}


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
            aspen.log_dammit(traceback)
        else:
            aspen.log_dammit(response.body)
    return {'traceback': None}


def delegate_error_to_simplate(website, request, response, resource=None):
    if response.code < 400:
        return

    code = str(response.code)
    possibles = [code + ".spt", "error.spt"]
    fspath = _first(website.ours_or_theirs(errpage) for errpage in possibles)

    if fspath is not None:
        request.original_resource = resource
        if resource is not None:
            # Try to return an error that matches the type of the original resource.
            request.headers['Accept'] = resource.media_type + ', text/plain; q=0.1'
        resource = resources.get(website, request)
        dispatch_result = DispatchResult(DispatchStatus.okay, fspath, {}, 'Found.', {})
        try:
            response = resource.respond(request, dispatch_result, response)
        except Response as response:
            if response.code != 406:
                raise

    return {'response': response, 'exception': None}


def log_traceback_for_exception(website, exception):
    tb = traceback.format_exc()
    aspen.log_dammit(tb)
    response = Response(500)
    if website.show_tracebacks:
        response.body = tb
    return {'response': response, 'exception': None}


def log_result_of_request(website, request=None, response=None):
    """Log access. With our own format (not Apache's).
    """

    if website.logging_threshold > 0: # short-circuit
        return


    # What was the URL path translated to?
    # ====================================

    if request is None:
        msg = "(no request available)"
    else:
        fs = getattr(request, 'fs', '')
        if fs.startswith(website.www_root):
            fs = fs[len(website.www_root):]
            if fs:
                fs = '.'+fs
        else:
            fs = '...' + fs[-21:]
        msg = "%-24s %s" % (request.line.uri.path.raw, fs)


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

    aspen.log("%-36s %s" % (response, msg))

"""
pando.algorithms.website
~~~~~~~~~~~~~~~~~~~~~~~~

These functions comprise the request processing functionality of Pando.

The order of functions in this module defines Pando algorithm for request
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

from aspen import resources
from aspen.http.resource import NegotiationFailure
from aspen.request_processor.dispatcher import (
    DispatchResult, DispatchStatus, NotFound, Redirect, UnindexedDirectory,
)
from first import first as _first

from .. import log as _log
from .. import log_dammit as _log_dammit
from .. import body_parsers
from ..http.request import Request
from ..http.response import Response


def parse_environ_into_request(environ):
    return {'request': Request.from_wsgi(environ)}


def insert_variables_for_aspen(request, website):
    return {
        'path': request.path,
        'querystring': request.qs,
        'request_processor': website.request_processor,
    }


def parse_body_into_request(request, website):
    request._parse_body = lambda _: body_parsers.parse_body( request.raw_body
                                                           , request.headers
                                                           , website.body_parsers
                                                            )


def request_available():
    """No-op placeholder for easy hookage"""
    pass


def raise_200_for_OPTIONS(request):
    """A hook to return 200 to an 'OPTIONS *' request"""
    if request.line.method == "OPTIONS" and request.line.uri == "*":
        raise Response(200)


def redirect_to_base_url(website, request):
    website.canonicalize_base_url(request)


# the following function is inserted here by `Website.__init__()`:
# aspen.request_processor.algorithm.dispatch_path_to_filesystem


def handle_dispatch_exception(website, exception):
    if isinstance(exception, Redirect):
        raise Response(302, exception.message)
    elif isinstance(exception, UnindexedDirectory) and website.list_directories:
        autoindex_spt = website.ours_or_theirs('autoindex.html.spt')
        dispatch_result = DispatchResult( DispatchStatus.okay
                                        , autoindex_spt
                                        , {}
                                        , 'Directory autoindex.'
                                        , {'autoindexdir': exception.message}
                                        , False
                                         )
        return {'dispatch_result': dispatch_result, 'exception': None}
    elif isinstance(exception, NotFound):
        raise Response(404)


# the following functions are inserted here by `Website.__init__()`:
# aspen.request_processor.algorithm.apply_typecasters_to_path
# aspen.request_processor.algorithm.load_resource_from_filesystem


def resource_available():
    """No-op placeholder for easy hookage"""
    pass


def extract_accept_from_request(request):
    return {'accept_header': request.headers.get(b'Accept')}


def create_response_object(state):
    state.setdefault('response', Response())


# the following function is inserted here by `Website.__init__()`:
# aspen.request_processor.algorithm.render_resource


def fill_response_with_output(output, response, request_processor):
    if not isinstance(output.body, bytes):
        output.charset = request_processor.charset_dynamic
        output.body = output.body.encode(output.charset)
    response.body = output.body
    if b'Content-Type' not in response.headers:
        ct = output.media_type
        if output.charset:
            ct += '; charset=' + output.charset
        response.headers[b'Content-Type'] = ct.encode('ascii')


def get_response_for_exception(website, exception):
    tb = traceback.format_exc()
    if isinstance(exception, Response):
        response = exception
    elif isinstance(exception, NotFound):
        response = Response(404)
    elif isinstance(exception, NegotiationFailure):
        response = Response(406, exception.message)
    else:
        response = Response(500)
        if website.show_tracebacks:
            response.body = tb
    return {'response': response, 'traceback': tb, 'exception': None}


def response_available():
    """No-op placeholder for easy hookage"""
    pass


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
        resource = resources.get(website.request_processor, fspath)
        state['dispatch_result'] = DispatchResult( DispatchStatus.okay
                                                 , fspath
                                                 , {}
                                                 , 'Found.'
                                                 , {}
                                                 , True
                                                  )
        # Try to return an error that matches the type of the response the
        # client would have received if the error didn't occur
        wanted = getattr(state.get('output'), 'media_type', None)
        wanted = (wanted + ',' if wanted else '') + 'text/plain;q=0.2,*/*;q=0.1'
        state['accept_header'] = wanted

        output = resource.render(state)
        fill_response_with_output(output, response, website.request_processor)

    return {'exception': None}


def log_traceback_for_exception(website, exception):
    if isinstance(exception, Response):
        response = exception
        if response.code < 500:
            return {'response': response, 'exception': None}
    else:
        response = Response(500)
    tb = traceback.format_exc()
    _log_dammit(tb)
    if website.show_tracebacks:
        response.body = tb
    return {'response': response, 'exception': None}


def log_result_of_request(website, request=None, dispatch_result=None, response=None):
    """Log access. With our own format (not Apache's).
    """

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

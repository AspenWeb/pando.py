"""These functions comprise the request processing functionality of Aspen.

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

import sys
import traceback

import aspen
from aspen import dispatcher, resources, sockets
from aspen.http.request import Request
from aspen.http.response import Response
from aspen.sockets.socket import Socket
from aspen import typecasting
from first import first as _first


def parse_environ_into_request(environ):
    return {'request': Request.from_wsgi(environ)}


def tack_website_onto_request(request, website):
    # XXX Why?
    request.website = website


def raise_200_for_OPTIONS(request):
    """A hook to return 200 to an 'OPTIONS *' request"""
    if request.line.method == "OPTIONS" and request.line.uri == "*":
        raise Response(200)


def dispatch_request_to_filesystem(request):
    dispatcher.dispatch(request)


def apply_typecasters_to_path(website, request):
    typecasting.apply_typecasters(website.typecasters, request.line.uri.path)


def get_response_for_socket(request):
    socket = sockets.get(request)
    if socket is None:
        # This is not a socket request.
        response = None
    elif isinstance(socket, Response):
        # Actually, this is a handshake request.
        response = socket
    else:
        assert isinstance(socket, Socket)  # sanity check
        # This is a socket ... request?
        response = socket.respond(request)
    return {'response': response}


def get_resource_for_request(request, response):
    if response is None:
        return {'resource': resources.get(request)}


def get_response_for_resource(request, resource=None):
    if resource is not None:
        return {'response': resource.respond(request)}


def get_response_for_exception(exception):
    if isinstance(exception, Response):
        response = exception
    else:
        response = Response(500, traceback.format_exc())
    return {'response': response, 'exception': None}


def log_traceback_for_5xx(response):
    if response.code >= 500:
        aspen.log_dammit(response.body)


def delegate_error_to_simplate(website, request, response):
    if response.code < 400:
        return

    code = str(response.code)
    possibles = [code + ".html", code + ".html.spt", "error.html", "error.html.spt"]
    fs = _first(website.ours_or_theirs(errpage) for errpage in possibles)

    if fs is not None:
        request.fs = fs
        request.original_resource = request.resource
        resource = resources.get(request)
        response = resource.respond(request, response)

    return {'response': response, 'exception': None}


def log_traceback_for_exception(website, exception):
    tb = traceback.format_exc()
    aspen.log_dammit(tb)
    response = Response(500)
    if website.show_tracebacks:
        response.body = tb
    return {'response': response, 'exception': None}


def log_result_of_request(website, response, request):
    """Log access. With our own format (not Apache's).
    """

    if website.logging_threshold > 0: # short-circuit
        return


    # What was the URL path translated to?
    # ====================================

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

    filename, linenum = response.whence_raised()
    if filename is not None:
        response = "%s (%s:%d)" % (response, filename, linenum)
    else:
        response = str(response)

    # Log it.
    # =======

    aspen.log("%-36s %s" % (response, msg))

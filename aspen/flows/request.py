"""These functions comprise the request processing functionality of Aspen.

Per the flow.py module, the functions defined in this present module are
executed in the order they're defined here, with dependencies injected as
specified in each function definition. Each function should return None, or a
dictionary that will be used to update the flow state in the calling routine.

The naming convention we've adopted for the functions in this file is:

    verb_object_preposition_object-of-preposition

For example:

    parse_environ_into_request

All four parts are a single word each (there are exactly three underscores in
each function name). This convention is intended to make function names easy to
understand and remember.

It's important that function names remain relatively stable over time, as
downstream applications are expected to insert their own functions into this
flow based on the names of our functions here. A change in function names or
ordering here would constitute a backwards-incompatible change.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

import aspen
from aspen import dispatcher, resources, sockets
from aspen.http.request import Request
from aspen.http.response import Response
from aspen.sockets.socket import Socket
from first import first as _first


def parse_environ_into_request(environ):
    return {'request': Request.from_wsgi(environ)}


def tack_website_onto_request(request, website):
    # XXX Why?
    request.website = website


def dispatch_request_to_filesystem(request):
    dispatcher.dispatch(request)


def get_response_for_socket(request):
    socket = sockets.get(request)
    if socket is None:
        # This is not a socket request.
        return

    if isinstance(socket, Response):
        # Actually, this is a handshake request.
        response = socket
    else:
        assert isinstance(socket, Socket)  # sanity check
        # This is a socket ... request?
        response = socket.respond(request)
    return {'response': response}


def get_response_for_resource(request, response):
    if response is not None:
        return

    resource = resources.get(request)
    response = resource.respond(request)
    return {'response': response}


def get_response_for_exception(exc_info):
    sys.exc_clear()
    if exc_info[0] is Response:
        response = exc_info[1]
    else:
        response = Response(500, exc_info[2])
    return {'response': response, 'exc_info': None}


def log_traceback_for_5xx(response):
    if response.code >= 500:
        aspen.log_dammit(response.body)


def delegate_error_to_simplate(website, request, response):
    if response.code < 400:
        return

    code = str(response.code)
    possibles = [code + ".html", code + ".html.spt", "exc_info.html", "exc_info.html.spt"]
    fs = _first(website.ours_or_theirs(errpage) for errpage in possibles)

    if fs is not None:
        request.fs = fs
        request.original_resource = request.resource
        request.resource = resources.get(request)
        response = request.resource.respond(request)

    return {'response': response, 'exc_info': None}


def log_traceback_for_exception(website, exc_info):
    sys.exc_clear()
    aspen.log_dammit(exc_info[2])
    response = Response(500)
    if website.show_tracebacks:
        response.body = exc_info[2]
    return {'response': response, 'exc_info': None}


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

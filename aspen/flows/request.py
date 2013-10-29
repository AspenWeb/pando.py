"""These functions comprise the request processing functionality of Aspen.

This is a mutilated hacked up version of the old website.py.

"""
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


def get_response_via_socket(request):
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


def get_response_via_resource(request, response):
    if response is not None:
        return

    resource = resources.get(request)
    response = resource.respond(request)
    return {'response': response}


def handle_exception(exc_info):
    sys.exc_clear()
    if exc_info[0] is Response:
        response = exc_info[1]
    else:
        response = Response(500, exc_info[2])
    return {'response': response, 'exc_info': None}


def log_tracebacks_for_500s(response):
    if response.code >= 500:
        aspen.log_dammit(response.body)


def run_error_response_through_simplate(website, request, response):
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


def handle_exception_2(website, exc_info):
    sys.exc_clear()
    aspen.log_dammit(exc_info[2])
    response = Response(500)
    if website.show_tracebacks:
        response.body = exc_info[2]
    return {'response': response, 'exc_info': None}


def log_access(website, response, request):
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

"""These functions comprise the request processing functionality of Aspen.

This is a mutilated hacked up version of the old website.py.

"""
import traceback

import aspen
from aspen import dispatcher, resources, sockets
from aspen.http.request import Request
from aspen.http.response import Response
from first import first


def parse_environ_into_request(environ):
    return {'request': Request.from_wsgi(environ)}


def tack_website_onto_request(request, website):
    request.website = website


def dispatch_request_to_filesystem(request):
    dispatcher.dispatch(request)


def get_a_socket_if_there_is_one(request):
    response_or_socket = sockets.get(request)
    if isinstance(response_or_socket, Response):
        # This is a handshake request.
        return {'response': response_or_socket}
    else:
        # This is a socket ... request?
        return {'socket': response_or_socket}


def get_a_resource_if_there_is_one(request, socket):
    if socket is None:
        return {'resource': resources.get(request)}


def respond_to_request_via_resource_or_socket(request, resource, socket):
    if resource is not None:
        assert socket is None
        response = resource.respond(request)
    else:
        assert socket is not None
        response = socket.respond(request)
    return {'response': response}


def convert_non_response_error_to_response_error(error, request):
    if not isinstance(error, Response):
        response = Response(500, traceback.format_exc())
        return {'error': response}


def log_tracebacks_for_500s(error):
    if error.code >= 500:
        aspen.log_dammit(error.tb)


def process_error_using_simplate(website, request, error):
    rc = str(error.code)
    possibles = [rc + ".html", rc + ".html.spt", "error.html", "error.html.spt"]
    fs = first(website.ours_or_theirs(errpage) for errpage in possibles)

    if fs is not None:
        request.fs = fs
        request.original_resource = request.resource
        request.resource = resources.get(request)
        response = request.resource.respond(request, error)

    return {'response': response, 'error': None}


def process_error_very_simply(website, error):
    tb = traceback.format_exc().strip()
    tbs = '\n\n'.join([tb, "... while handling ...", error.tb])
    aspen.log_dammit(tbs)
    response = Response(500)
    if website.show_tracebacks:
        response.body = tbs
    return {'response': response, 'error': None}


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

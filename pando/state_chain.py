"""
:mod:`state_chain`
------------------

These functions comprise the request processing functionality of Pando.

The order of functions in this module defines Pando's state chain for request
processing. The actual parsing is done by `StateChain.from_dotted_name()
<https://state-chain-py.readthedocs.io/en/latest/#state_chain.StateChain.from_dotted_name>`_.

Dependencies are injected as specified in each function definition. Each function
should return :obj:`None`, or a dictionary that will be used to update the
state in the calling routine.

It's important that function names remain relatively stable over time, as
downstream applications are expected to insert their own functions into this
chain based on the names of our functions here. A change in function names
or ordering here would constitute a backwards-incompatible change.

"""

import os
import os.path
import traceback

from aspen.exceptions import NegotiationFailure, NotFound
from aspen.http.resource import Static
from aspen.request_processor import typecasting
from aspen.request_processor.dispatcher import DispatchResult, DispatchStatus
from first import first as _first

from .logging import log as _log
from .logging import log_dammit as _log_dammit
from .http.request import Request
from .http.response import Response


def parse_environ_into_request(environ, website):
    return {'request': Request.from_wsgi(website, environ)}


def request_available():
    """No-op placeholder for easy hookage"""
    pass


def raise_204_for_OPTIONS(request):
    """Return a 204 (No Content) for all OPTIONS requests.

    Ideally a response to an OPTIONS request for a specific URL would include an
    `Allow` header listing all the valid request methods for that URL, but we
    currently don't have a simple and efficient way of getting that list.

    Doc: https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/OPTIONS
    """
    if request and request.line.method == b"OPTIONS":
        raise Response(204)


def redirect_to_base_url(website, request):
    website.canonicalize_base_url(request)


def dispatch_path_to_filesystem(website, request):
    return {'dispatch_result': website.request_processor.dispatch(request.path)}


def raise_404_if_missing(dispatch_result, website):
    if dispatch_result.status == DispatchStatus.missing:
        raise Response(404)


def redirect_to_canonical_path(dispatch_result, website):
    if dispatch_result.canonical:
        website.redirect(dispatch_result.canonical)


def apply_typecasters_to_path(state, website, request):
    typecasting.apply_typecasters(
        website.request_processor.typecasters, request.path, state
    )


def load_resource_from_filesystem(website, dispatch_result):
    fspath = dispatch_result.match
    if dispatch_result.status == DispatchStatus.unindexed:
        if website.list_directories:
            fspath = website.ours_or_theirs('autoindex.html.spt')
        else:
            raise Response(404)
    return {'resource': website.request_processor.resources.get(fspath)}


def resource_available():
    """No-op placeholder for easy hookage"""
    pass


def create_response_object(state):
    state.setdefault('response', Response())


def extract_accept_header(request=None, exception=None):
    if not request:
        return
    accept_header = request.headers.get(b'Accept') or None
    if accept_header:
        accept_header = accept_header.decode('ascii', 'backslashreplace')
    return {'accept_header': accept_header}


def render_response(state, resource, response, website):
    if isinstance(resource, Static):
        method = getattr(state.get('request'), 'method', 'GET')
        if method == 'GET':
            output = resource.render()
        elif method == 'HEAD':
            if b'Content-Length' not in response.headers:
                if resource.raw is not None:
                    length = len(resource.raw)
                else:
                    length = os.stat(resource.fspath).st_size
                response.headers[b'Content-Length'] = str(length).encode('ascii')
            return
        else:
            raise Response(405)
    else:
        context = dict(state)  # copy to avoid unintended modifications by simplates
        output = None
        try:
            output = resource.render(context, state['dispatch_result'], state['accept_header'])
        finally:
            state['output'] = output or context.get('output')

    if not isinstance(output.body, bytes):
        if not output.charset:
            output.charset = website.request_processor.encode_output_as
        output.body = output.body.encode(output.charset)
    response.body = output.body

    if b'Content-Type' not in response.headers:
        media_type = output.media_type
        if output.charset:
            media_type += '; charset=' + output.charset
        response.headers[b'Content-Type'] = media_type.encode('ascii')


def handle_negotiation_exception(exception):
    if isinstance(exception, NotFound):
        response = Response(404)
    elif isinstance(exception, NegotiationFailure):
        response = Response(406, exception.message)
    else:
        return
    return {'response': response, 'exception': None}


def get_response_for_exception(website, exception):
    tb = traceback.format_exc()
    if isinstance(exception, Response):
        response = exception
        response.set_whence_raised()
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
        resource = website.request_processor.resources.get(fspath)
        state['dispatch_result'] = DispatchResult(
            DispatchStatus.okay, fspath, None, None, None
        )
        # Try to return an error that matches the type of the response the
        # client would have received if the error didn't occur
        wanted = getattr(state.get('output'), 'media_type', None) or ''
        # If we don't have a media type (e.g. when we're returning a 404), then
        # we fall back to the Accept header
        if state.get('accept_header'):
            wanted += ',' + state['accept_header']
        # As a last resort we accept anything, with a preference for text/plain
        wanted += ',text/plain;q=0.2,*/*;q=0.1'
        state['accept_header'] = wanted.lstrip(',')

        render_response(state, resource, response, website)


def log_traceback_for_exception(website, exception):
    if isinstance(exception, Response):
        response = exception
        response.set_whence_raised()
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
        msg = "%-24s %s" % (request.line.uri.path.decoded, fspath)

    # Where was response raised from?
    # ===============================

    if response is None:
        status = "(no response available)"
    else:
        status = response._status_text()
        filename, linenum = response.whence_raised
        if filename is not None:
            status += " (%s:%d)" % (filename, linenum)

    # Log it.
    # =======

    # INFO when code < 400, WARNING when < 500, ERROR when < 600, CRITICAL when
    # we don't have a response code
    level = max((getattr(response, 'code', 600) - 100) // 100 * 10, 20)
    _log("%-36s %s" % (status, msg), level=level)

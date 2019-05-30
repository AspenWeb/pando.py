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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import os.path
import traceback

from aspen import resources
from aspen.exceptions import NegotiationFailure, NotFound
from aspen.http.resource import Static
from aspen.request_processor.dispatcher import DispatchResult, DispatchStatus
from first import first as _first

from .logging import log as _log
from .logging import log_dammit as _log_dammit
from .http.request import Request
from .http.response import Response
from .utils import _import_from


def parse_environ_into_request(environ, website):
    return {'request': Request.from_wsgi(website, environ)}


def insert_variables_for_aspen(request, website):
    accept = request.headers.get(b'Accept')
    return {
        'accept_header': None if accept is None else accept.decode('ascii', 'backslashreplace'),
        'path': request.path,
        'querystring': request.qs,
        'request_processor': website.request_processor,
    }


def request_available():
    """No-op placeholder for easy hookage"""
    pass


def raise_200_for_OPTIONS(request):
    r"""A hook to return 200 to an 'OPTIONS \*' request"""
    if request.line.method == b"OPTIONS" and request.line.uri == b"*":
        raise Response(200)


def redirect_to_base_url(website, request):
    website.canonicalize_base_url(request)


@_import_from('aspen.request_processor.algorithm')
def dispatch_path_to_filesystem():
    pass


def handle_dispatch_errors(dispatch_result, website):
    if dispatch_result.canonical:
        website.redirect(dispatch_result.canonical)
    elif dispatch_result.status == DispatchStatus.unindexed and website.list_directories:
        autoindex_spt = website.ours_or_theirs('autoindex.html.spt')
        dispatch_result = DispatchResult(
            DispatchStatus.okay, autoindex_spt, dispatch_result.wildcards,
            dispatch_result.extension, dispatch_result.match
        )
        return {'dispatch_result': dispatch_result}
    elif dispatch_result.status != DispatchStatus.okay:
        raise Response(404)


@_import_from('aspen.request_processor.algorithm')
def apply_typecasters_to_path():
    pass


@_import_from('aspen.request_processor.algorithm')
def load_resource_from_filesystem():
    pass


def resource_available():
    """No-op placeholder for easy hookage"""
    pass


def create_response_object(state):
    state.setdefault('response', Response())


def render_response(state, resource, response, request_processor):
    if isinstance(resource, Static):
        if state['request'].method == 'GET':
            if resource.raw is not None:
                response.body = resource.raw
            else:
                fspath = os.path.realpath(resource.fspath)
                if not fspath.startswith(request_processor.www_root):
                    raise Response(500, "resource is outside www_root")
                with open(fspath, 'rb') as f:
                    response.body = f.read()
        elif state['request'].method == 'HEAD':
            if resource.raw is not None:
                length = len(resource.raw)
            else:
                length = os.stat(resource.fspath).st_size
            response.headers[b'Content-Length'] = str(length).encode('ascii')
        else:
            raise Response(405)
        media_type, charset = resource.media_type, resource.charset
    else:
        output = resource.render(state)
        if not isinstance(output.body, bytes):
            output.charset = request_processor.encode_output_as
            output.body = output.body.encode(output.charset)
        media_type, charset = output.media_type, output.charset
        response.body = output.body
    if b'Content-Type' not in response.headers:
        if charset:
            media_type += '; charset=' + charset
        response.headers[b'Content-Type'] = media_type.encode('ascii')


def get_response_for_exception(website, exception):
    tb = traceback.format_exc()
    if isinstance(exception, Response):
        response = exception
        response.set_whence_raised()
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
        state['dispatch_result'] = DispatchResult(
            DispatchStatus.okay, fspath, None, None, None
        )
        # Try to return an error that matches the type of the response the
        # client would have received if the error didn't occur
        wanted = getattr(state.get('output'), 'media_type', None) or ''
        # If we don't have a media type (e.g. when we're returning a 404), then
        # we fall back to the Accept header
        wanted += ',' + (state.get('accept_header') or '')
        # As a last resort we accept anything, with a preference for text/plain
        wanted += ',text/plain;q=0.2,*/*;q=0.1'
        state['accept_header'] = wanted.lstrip(',')

        render_response(state, resource, response, website.request_processor)


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

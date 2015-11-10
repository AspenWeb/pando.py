"""
aspen.algorithm
~~~~~~~~~~~~~~~

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


from . import dispatcher, resources, body_parsers, typecasting
from .http.request import Request
from .http.response import Response


def parse_environ_into_request(environ):
    return {'request': Request.from_wsgi(environ)}


def parse_body_into_request(request, website):
    request._parse_body = lambda _: body_parsers.parse_body( request.raw_body
                                                           , request.headers
                                                           , website.body_parsers
                                                            )


def request_available():
    """No-op placeholder for easy hookage"""
    pass


def dispatch_request_to_filesystem(website, request):

    try:
        result = dispatcher.dispatch( indices               = website.indices
                                    , media_type_default    = website.media_type_default
                                    , pathparts             = request.line.uri.path.parts
                                    , uripath               = request.line.uri.path.raw
                                    , querystring           = request.line.uri.querystring.raw
                                    , startdir              = website.www_root
                                     )
    except dispatcher.Redirect as err:
        website.redirect(err.msg)
    except dispatcher.NotFound:
        raise Response(404)
    except dispatcher.DispatchError as err:
        raise Response(500, body=err.msg)

    for k, v in result.wildcards.iteritems():
        request.line.uri.path[k] = v
    return {'dispatch_result': result}


def apply_typecasters_to_path(website, request, state):
    try:
        typecasting.apply_typecasters( website.typecasters
                                     , request.line.uri.path
                                     , state
                                      )
    except typecasting.TypecastError:
        raise Response(404)


def get_resource_for_request(website, dispatch_result):
    return {'resource': resources.get(website, dispatch_result.match)}


def resource_available():
    """No-op placeholder for easy hookage"""
    pass


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


def response_available():
    """No-op placeholder for easy hookage"""
    pass

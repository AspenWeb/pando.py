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

from . import dispatcher, resources, typecasting
from .http.request import Path, Querystring
from .http.response import Response


def hydrate_path(path):
    return {'path': Path(path)}


def hydrate_querystring(querystring):
    return {'querystring': Querystring(querystring)}


def dispatch_path_to_filesystem(website, path, querystring):
    result = dispatcher.dispatch( indices               = website.indices
                                , media_type_default    = website.media_type_default
                                , pathparts             = path.parts
                                , uripath               = path.decoded
                                , startdir              = website.www_root
                                 )
    for k, v in result.wildcards.iteritems():
        path[k] = v
    return {'dispatch_result': result}


def apply_typecasters_to_path(website, path, state):
    typecasting.apply_typecasters( website.typecasters
                                 , path
                                 , state
                                  )


def get_resource_for_request(website, dispatch_result):
    return {'resource': resources.get(website, dispatch_result.match)}


def resource_available():
    """No-op placeholder for easy hookage"""
    pass


def get_response_for_resource(state, website, resource=None):
    if resource is not None:
        state.setdefault('response', Response(charset=website.charset_dynamic))
        return {'response': resource.respond(state)}


def response_available():
    """No-op placeholder for easy hookage"""
    pass

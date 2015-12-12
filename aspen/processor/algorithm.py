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

from . import dispatcher, typecasting
from .. import resources, output
from ..http.request import Path, Querystring


def hydrate_path(path):
    return {'path': Path(path)}


def hydrate_querystring(querystring):
    return {'querystring': Querystring(querystring)}


def dispatch_path_to_filesystem(processor, path, querystring):
    result = dispatcher.dispatch( indices               = processor.indices
                                , media_type_default    = processor.media_type_default
                                , pathparts             = path.parts
                                , uripath               = path.decoded
                                , startdir              = processor.www_root
                                 )
    for k, v in result.wildcards.iteritems():
        path[k] = v
    return {'dispatch_result': result}


def apply_typecasters_to_path(processor, path, state):
    typecasting.apply_typecasters( processor.typecasters
                                 , path
                                 , state
                                  )


def load_resource_from_filesystem(processor, dispatch_result):
    return {'resource': resources.get(processor, dispatch_result.match)}


def render_resource(state, processor, resource):
    state.setdefault('output', output.Output(charset=processor.charset_dynamic))
    return {'output': resource.render(state)}

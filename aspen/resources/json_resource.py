import datetime

from aspen import json
from aspen.resources.dynamic_resource import DynamicResource


class FriendlyEncoder(json.JSONEncoder):
    """Add support for additional types to the default JSON encoder.
    """

    def default(self, obj):
        if isinstance(obj, complex):
            # http://docs.python.org/library/json.html
            out = [obj.real, obj.imag]
        elif isinstance(obj, datetime.datetime):
            # http://stackoverflow.com/questions/455580/
            out = obj.isoformat()
        else:
            out = json.JSONEncoder.default(self, obj)
        return out


class JSONResource(DynamicResource):

    def __init__(self, *a, **kw):
        """By now we know that we're not static, so check for the json module.
        """
        if json is None:
            raise LoadError("Neither json nor simplejson was found. Try "
                            "installing simplejson to use dynamic JSON "
                            "resources. See "
                            "http://aspen.io/resources/json/#libraries for "
                            "more information.")
        super(JSONResource, self).__init__(*a, **kw)

    def compile(self, npages, pages):
        """Given an int and a sequence of bytestrings, set attributes on self.
        """
        if npages == 2:
            one, two = pages
        else:
            raise SyntaxError( "JSON resources must have exactly two pages; "
                               "%s has %d." % (self.fs, npages)
                              )
       
        one, two = self.compile_python(one, two)
        self.one = one
        self.two = two
  
    def mutate(self, namespace):
        """Given a namespace dict, mutate it.
        """
        response = namespace['response']
        if not isinstance(response.body, basestring):
            response.body = json.dumps( response.body
                                      , cls=FriendlyEncoder
                                       )
        response.headers.set('Content-Type', self.website.json_content_type)

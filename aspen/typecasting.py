from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import Response

"""
Pluggable typecasting of virtual path values

"""

class FailedTypecast(Response):
    def __init__(self, extension):
        body = "Failure to typecast extension '{0}'".format(extension)
        Response.__init__(self, code=404, body=body)

"""typecast is a map of suffix -> typecasting function.
   The functions must take one unicode argument, but may return
   any value.  If they raise an error, the result will not be used
   and the typecasted key (the one without the suffix) will not
   be set
"""
defaults = { 'int': int
           , 'float': float
           }

def apply_typecasters(typecasters, path):
    """Perform the typecasts (in-place!) on the supplied path Mapping.
       Note that the supplied mapping has keys with the typecast extensions
       still attached (and unicode values).  This routine adds keys 
       *without* those extensions attached anymore, but with typecast values.
    """
    for part in path.keys():
        pieces = part.rsplit('.',1)
        if len(pieces) > 1:
            var, ext = pieces
            if ext in typecasters:
                try:
                    # path is a Mapping not a dict, so:
                    for v in path.all(part):
                        path.add(var, typecasters[ext](v))
                    path.popall(part)
                except:
                    raise FailedTypecast(ext)


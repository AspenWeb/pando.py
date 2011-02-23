import os.path
from collections import Callable

from aspen.configuration.colon import colonize
from aspen.configuration.exceptions import ConfFileError


FORM_FEED = chr(12)


def load_middleware(*filenames):
    """Given a list of filenames, return two lists.

    The file format for middleware.conf is a double-newline separated list of 
    inbound and then outbound middlewares, like so:
        
        my.first.middleware:inbound
        my.second.middleware:inbound

        my.second.middleware:outbound

    """
    class Middleware(list): # weird, but makes testing nice and API nice
        @property
        def inbound(self):
            return self[0]
        @property
        def outbound(self):
            return self[1]


    class Section(list):
        def append_if(self, line, path, i):
            line = line.split('#', 1)[0].strip()
            if line: 
                obj = colonize(line, path, i)
                if not isinstance(obj, Callable):
                    raise ConfFileError( "'%s' is not callable." % line
                                       , path
                                       , i
                                        )
                self.append(obj)

    inbound = Section()
    outbound = Section()
    middleware = Middleware([inbound, outbound])

    for path in filenames:
        current = inbound
        if not os.path.isfile(path):
            continue
        i = 0
        for line in open(path):
            i += 1
            if FORM_FEED in line:
                before, after = line.split(FORM_FEED)
                current.append_if(before, path, i)
                if outbound is current:
                    break # ignore rest of file
                current = outbound
                current.append_if(after, path, i)
            else:
                current.append_if(line, path, i)

    return middleware

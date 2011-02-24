import os.path
from collections import Callable

from aspen.configuration.colon import colonize
from aspen.configuration.exceptions import ConfFileError


FORM_FEED = chr(12)


def HooksConf(*filenames):
    """Given a list of filenames, return three lists.

    The file format for hooks.conf is a double-newline separated list of 
    inbound and then outbound hookss, like so:
        
        my.first.hooks:inbound
        my.second.hooks:inbound

        my.second.hooks:outbound

    """
    class Hooks(list): # sure, kind of weird, but makes testing and API nice 
        @property
        def startup(self):
            return self[0]
        @property
        def inbound(self):
            return self[1]
        @property
        def outbound(self):
            return self[2]
        @property
        def shutdown(self):
            return self[3]


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

    startup = Section()
    inbound = Section()
    outbound = Section()
    shutdown = Section()
    hooks = Hooks([startup, inbound, outbound, shutdown])

    for path in filenames:
        current = startup 
        if not os.path.isfile(path):
            continue
        i = 0
        for line in open(path):
            i += 1
            if FORM_FEED in line:
                before, after = line.split(FORM_FEED)
                current.append_if(before, path, i)
                if startup is current:
                    current = inbound 
                elif inbound is current:
                    current = outbound 
                elif outbound is current:
                    current = shutdown 
                elif shutdown is current:
                    break # ignore rest of file
                current.append_if(after, path, i)
            else:
                current.append_if(line, path, i)

    return hooks

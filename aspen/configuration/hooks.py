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
    SECTIONS = [ 'startup'
               , 'inbound_early'    # _ instead of . to harmonize w/ docs,
               , 'inbound_late'     # where we talk in terms of a function
               , 'outbound_early'   # named thus.
               , 'outbound_late'
               , 'shutdown'
                ]

    class Hooks(list):

        def __init__(self, spec):
            """Takes a list of 2-tuples, (name, Section).
            """
            list.__init__(self)
            self._by_name = dict()
            for name, section in spec:
                self.append(section)
                self._by_name[name] = section

        def run(self, name, thing):
            """Takes a section name an request/response/website.
            """
            section = self._by_name[name]
            for hook in section:
                thing = hook(thing) or thing
            return thing
    
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

    hooks = Hooks([(name, Section()) for name in SECTIONS])

    for path in filenames:
        current = hooks[0] 
        if not os.path.isfile(path):
            continue
        i = 0
        for line in open(path):
            i += 1
            if FORM_FEED in line:
                before, after = line.split(FORM_FEED)
                current.append_if(before, path, i)
                if current is hooks[-1]:
                    break # ignore rest of file
                current = hooks[hooks.index(current) + 1]
                current.append_if(after, path, i)
            else:
                current.append_if(line, path, i)

    return hooks

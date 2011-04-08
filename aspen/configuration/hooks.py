import os.path
from collections import Callable

from aspen.configuration.colon import colonize
from aspen.configuration.exceptions import ConfFileError


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
        """Takes a section name and request/response/website.
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
                                   , i
                                   , path
                                    )
            self.append(obj)

class Done(Exception):
    pass    

def HooksConf(page_break, *filenames):
    """Given a page_break character and a list of filenames, return six lists.

    The file format for hooks.conf is a ^L-separated list of hooks, like so:
      
        startup:hook
        ^L
        my.first.hooks:inbound
        my.second.hooks:inbound
        ^L
        my.second.hooks:outbound

    """
    SECTIONS = [ 'startup'
               , 'inbound_early'    # _ instead of . to harmonize w/ docs,
               , 'inbound_late'     # where we talk in terms of functions
               , 'outbound_early'   # named thus.
               , 'outbound_late'
               , 'shutdown'
                ]

    hooks = Hooks([(name, Section()) for name in SECTIONS])

    for path in filenames:
        current = hooks[0] 
        if not os.path.isfile(path):
            continue
        i = 0
        try:
            for line in open(path):
                i += 1
                while page_break in line:
                    before, line = line.split(page_break, 1)
                    current.append_if(before, path, i)
                    if current is hooks[-1]:
                        raise Done # ignore rest of file
                    current = hooks[hooks.index(current) + 1]
                current.append_if(line, path, i)
        except Done:
            pass

    return hooks

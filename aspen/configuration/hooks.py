import os.path
try:                # Python >= 2.6
    from collections import Callable
    def isCallable(obj):
        return isinstance(obj, Callable)
except ImportError: # Python < 2.6
    from operator import isCallable

from aspen.configuration.colon import colonize
from aspen.configuration.exceptions import ConfFileError


PAGE_BREAK = chr(12)


class Hooks(list):

    def __init__(self, spec):
        """Takes a list of 2-tuples, (name, Section).
        """
        list.__init__(self)
        self._by_name = dict()
        for name, section in spec:
            self.append(section)
            self._by_name[name] = section

    def index(self, section):
        """Override list.index to test for identity and not just equality.

        If we just take the default list.index implementation, then
        non-identical sections will be conflated. This can happen easily, as
        empty sections will evaluate equal.

        https://github.com/whit537/aspen/issues/9

        """
        for i in range(len(self)):
            if self[i] is section:
                return i
        return -1

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
            if not isCallable(obj):
                raise ConfFileError( "'%s' is not callable." % line
                                   , i
                                   , path
                                    )
            self.append(obj)

class Done(Exception):
    pass

def HooksConf(*filenames):
    """Given a list of filenames, return six lists.

    The file format for hooks.conf is a ^L-separated list of hooks, like so:
      
        startup:hook
        ^L
        my.first.hooks:inbound
        my.second.hooks:inbound
        ^L
        my.second.hooks:outbound

    If literal ^ and L are used, they are converted to page breaks and
    processed accordingly.

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
                while '^L' in line:
                    line = line.replace('^L', PAGE_BREAK)
                i += 1
                while PAGE_BREAK in line:
                    before, line = line.split(PAGE_BREAK, 1)
                    current.append_if(before, path, i)
                    if current is hooks[-1]:
                        raise Done # ignore rest of file
                    current = hooks[hooks.index(current) + 1]
                current.append_if(line, path, i)
        except Done:
            pass

    return hooks

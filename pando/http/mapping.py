"""
pando.http.mapping
~~~~~~~~~~~~~~~~~~
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen.http.mapping import Mapping as _Mapping


class Mapping(_Mapping):

    def keyerror(self, name):
        from .response import Response
        raise Response(400, "Missing key: %s" % repr(name))


class CaseInsensitiveMapping(Mapping):

    def __init__(self, *a, **kw):
        for it in a:
            if it is None:
                continue
            items = it.items() if hasattr(it, 'items') else it
            for k, v in items:
                self[k] = v
        for k, v in kw.items():
            self[k] = v

    def __contains__(self, name):
        return Mapping.__contains__(self, name.title())

    def __getitem__(self, name):
        return Mapping.__getitem__(self, name.title())

    def __setitem__(self, name, value):
        return Mapping.__setitem__(self, name.title(), value)

    def add(self, name, value):
        return Mapping.add(self, name.title(), value)

    def get(self, name, default=None):
        return Mapping.get(self, name.title(), default)

    def all(self, name):
        return Mapping.all(self, name.title())

    def pop(self, name):
        return Mapping.pop(self, name.title())

    def popall(self, name):
        return Mapping.popall(self, name.title())

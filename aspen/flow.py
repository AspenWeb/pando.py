"""Implement a linear control flow model.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import types
import traceback
from collections import namedtuple


class FunctionNotFound(Exception):
    def __str__(self):
        return "The function '{}' isn't in this flow.".format(*self.args)


class Flow(object):

    want_short_circuit = False

    def __init__(self, dotted_name):
        self.module = self._load_module_from_dotted_name(dotted_name)
        self.functions = self._load_functions_from_module(self.module)


    def __iter__(self):
        return iter(self.functions)


    def get_names(self):
        return [f.func_name for f in self]


    def insert_after(self, newfunc, name):
        self.insert_relative_to(newfunc, name, relative_position=1)


    def insert_before(self, newfunc, name):
        self.insert_relative_to(newfunc, name, relative_position=-1)


    def insert_relative_to(self, newfunc, name, relative_position):
        func = self.resolve_name_to_function(name)
        index = self.functions.index(func) + relative_position
        self.functions.insert(index, newfunc)


    def remove(self, name):
        func = self.resolve_name_to_function(name)
        self.functions.remove(func)


    def resolve_name_to_function(self, name):
        func = None
        for func in self.functions:
            if func.func_name == name:
                break
        if func is None:
            raise FunctionNotFound(name)
        return func


    def run(self, state, through=None):
        """
        """
        if through is not None:
            if through not in self.get_names():
                raise FunctionNotFound(through)
        print()
        for function in self.functions:
            function_name = function.func_name
            try:
                if 'exc_info' not in state:
                    state['exc_info'] = None
                deps = self._resolve_dependencies(function, state)
                if 'exc_info' in deps.required and state['exc_info'] is None:
                    pass    # Hook needs an exc_info but we don't have it.
                    print("{:>48}  \x1b[33;1mskipped\x1b[0m".format(function_name))
                elif 'exc_info' not in deps.names and state['exc_info'] is not None:
                    pass    # Hook doesn't want an exc_info but we have it.
                    print("{:>48}  \x1b[33;1mskipped\x1b[0m".format(function_name))
                else:
                    new_state = function(**deps.kw)
                    print("{:>48}  \x1b[32;1mdone\x1b[0m".format(function_name))
                    if new_state is not None:
                        state.update(new_state)
            except:
                print("{:>48}  \x1b[31;1mfailed\x1b[0m".format(function_name))
                state['exc_info'] = sys.exc_info()[:2] + (traceback.format_exc().strip(),)
                if self.want_short_circuit:
                    raise

            if through is not None and function_name == through:
                break

        if state['exc_info'] is not None:
            raise

        return state


    # Helpers for loading from a file.
    # ================================

    def _load_module_from_dotted_name(self, dotted_name):
        class Module(object): pass
        module = Module()  # let's us use getattr to traverse down
        exec 'import {}'.format(dotted_name) in module.__dict__
        for name in dotted_name.split('.'):
            module = getattr(module, name)
        return module


    def _load_functions_from_module(self, module):
        """Given a module object, return a list of functions from the module, sorted by lineno.
        """
        functions_with_lineno = []
        for name in dir(module):
            if name.startswith('_'):
                continue
            obj = getattr(module, name)
            if type(obj) != types.FunctionType:
                continue
            func = obj
            lineno = func.func_code.co_firstlineno
            functions_with_lineno.append((lineno, func))
        functions_with_lineno.sort()
        return [func for lineno, func in functions_with_lineno]


    # Helpers for dependency injection.
    # =================================

    @staticmethod
    def _parse_signature(function):
        """Given a function, return a tuple of required args and dict of optional args.
        """
        code = function.func_code
        varnames = code.co_varnames[:code.co_argcount]

        nrequired = len(varnames)
        values = function.func_defaults
        optional = {}
        if values is not None:
            nrequired = -len(values)
            keys = varnames[nrequired:]
            optional = dict(zip(keys, values))

        required = varnames[:nrequired]

        return varnames, required, optional


    @classmethod
    def _resolve_dependencies(cls, function, available):
        """Given a function and a dict of available deps, return a deps object.

        The deps object has these attributes:

            a - a tuple of argument values
            kw - a dictionary of keyword arguments
            names - a tuple of the names of all arguments (in order)
            required - a tuple of names of required arguments (in order)
            optional - a dictionary of names of optional arguments with their
                         default values

        """
        deps = namedtuple('deps', 'a kw names required optional')
        deps.a = tuple()
        deps.kw = {}
        deps.names, deps.required, deps.optional = cls._parse_signature(function)

        missing = object()
        for name in deps.names:
            value = missing  # don't use .get, to avoid bugs around None
            if name in available:
                value = available[name]
            elif name in deps.optional:
                value = deps.optional[name]
            if value is not missing:
                deps.a += (value,)
                deps.kw[name] = value
        return deps

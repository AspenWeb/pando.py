from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import types
from collections import namedtuple


class FunctionNotFound(Exception):
    def __str__(self):
        return "The function {} isn't in this list.".format(*self.args)


class Flow(object):

    def __init__(self, dotted_name):
        self.module = self._load_module_from_dotted_name(dotted_name)
        self.functions = self._load_functions_from_module(self.module)


    def __iter__(self):
        return iter(self.functions)


    def get_names(self):
        return [f.func_name for f in self]


    def insert_after(self, newfunc, name):
        self.insert(newfunc, name, relative_position=1)


    def insert_before(self, newfunc, name):
        self.insert(newfunc, name, relative_position=-1)


    def insert_relative_to(self, newfunc, name, relative_position):
        func = None
        for func in self.functions:
            if func.func_name == name:
                break
        if func is None:
            raise FunctionNotFound(name)
        index = self.functions.indexOf(func) + relative_position
        self.functions.insert(index, newfunc)


    def run(self, state, through=None):
        """
        """
        print()
        for function in self.functions:
            function_name = function.func_name
            try:
                if 'error' not in state:
                    state['error'] = None
                deps = self._resolve_dependencies(function, state)
                if 'error' in deps.required and state['error'] is None:
                    pass    # Hook needs an error but we don't have it.
                    print("{:>48}  \x1b[33;1mskipped\x1b[0m".format(function_name))
                elif 'error' not in deps.names and state['error'] is not None:
                    pass    # Hook doesn't want an error but we have it.
                    print("{:>48}  \x1b[33;1mskipped\x1b[0m".format(function_name))
                else:
                    new_state = function(**deps.kw)
                    print("{:>48}  \x1b[32;1mdone\x1b[0m".format(function_name))
                    if new_state is not None:
                        state.update(new_state)
            except:
                print("{:>48}  \x1b[31;1mfailed\x1b[0m".format(function_name))
                state['error'] = sys.exc_info()[1]
            if through is not None and function_name == through:
                break

        if state['error'] is not None:
            raise

        return state


    # Helpers for loading from a file.
    # ================================

    def _load_module_from_dotted_name(self, dotted_name):
        from_clause, import_clause = dotted_name.rsplit('.', 1)
        capture = {}
        exec 'from {} import {}'.format(from_clause, import_clause) in capture
        module = capture[import_clause]
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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import re


def by_lambda(filter_lambda):
    def wrap(flow_step):
        def wrapped_flow_step_by_lambda(*args,**kwargs):
            if filter_lambda():
                return flow_step(*args,**kwargs)
        wrapped_flow_step_by_lambda.func_name = flow_step.func_name
        return wrapped_flow_step_by_lambda
    return wrap


def by_regex(regex_tuples, default=True):
    """A filter for flow steps.

    regex_tuples is a list of (regex, filter?) where if the regex matches the
    requested URI, then the flow is applied or not based on if filter? is True
    or False.

    For example:

        from aspen.flows.filter import by_regex

        @by_regex( ( ("/secret/agenda", True), ( "/secret.*", False ) ) )
        def use_public_formatting(request):
            ...

    would call the 'use_public_formatting' flow step only on /secret/agenda
    and any other URLs not starting with /secret.

    """
    regex_res = [ (re.compile(regex), disposition) \
                           for regex, disposition in regex_tuples.iteritems() ]
    def filter_flow_step(flow_step):
        def flow_step_filter(request, *args):
            for regex, disposition in regex_res:
                if regex.matches(request.line.uri):
                    if disposition:
                        return flow_step(*args)
            if default:
                return flow_step(*args)
        flow_step_filter.func_name = flow_step.func_name
        return flow_step_filter
    return filter_flow_step


def by_dict(truthdict, default=True):
    """A filter for hooks.

    truthdict is a mapping of URI -> filter? where if the requested URI is a
    key in the dict, then the hook is applied based on the filter? value.

    """
    def filter_flow_step(flow_step):
        def flow_step_filter(request, *args):
            do_hook = truthdict.get(request.line.uri, default)
            if do_hook:
                return flow_step(*args)
        flow_step_filter.func_name = flow_step.func_name
        return flow_step_filter
    return filter_flow_step

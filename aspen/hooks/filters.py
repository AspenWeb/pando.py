import re


def by_regex(hook, regex_tuples, default=True):
    """A filter for hooks. regex_tuples is a list of (regex, filter?) where if the regex matches
       the requested URI, then the hook is applied or not based on if filter? is True or False.
    """
    regex_res = [ (re.compile(regex), disposition) for regex, disposition in regex_tuples.iteritems() ]
    def filtered_hook(request):
        for regex, disposition in regex_res:
            if regex.matches(request.line.uri):
                if disposition:
                    return hook(request)
                else:
                    return request
        return default
    return filtered_hook


def by_dict(hook, truthdict, default=True):
    """A filter for hooks.

    truthdict is a mapping of URI -> filter? where if the requested URI is a key in the dict, then
    the hook is applied based on the filter? value.
    """
    def filtered_hook(request):
        do_hook = truthdict.get(request.line.uri, default)
        if do_hook:
            return hook(request)
        else:
            return request
    return filtered_hook

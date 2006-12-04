"""Rules distributed with Aspen.

Rules take a file object and predicate, and return a boolean.

"""
import commands
import fnmatch as _fnmatch
import mimetypes
import re
import os

from aspen.exceptions import RuleError


# Helper
# ======

def what_we_want(predicate):
    """Given a predicate value, return a boolean interpretation.

    This is to be called from other rule callables, where the predicate is one
    of true/yes/1 or false/no/none/0. If no predicate was given in the conf
    file, then we will receive None here, which becomes True.

    So the basic usage pattern is:

        >>> def rule(path, predicate):
        >>>     some_condition = my_test(path)
        >>>     return some_condition is what_we_want(predicate)
        ...

    """
    if predicate is None:
        out = True
    else:
        predicate = predicate.lower()
        if predicate in ('true', 'yes', '1'):
            out = True
        elif predicate in ('false', 'no', 'none', '0'):
            out = False
        else:
            raise RuleError('predicate must be true/yes/1 or false/no/none/0')
    return out



# Rules
# =====

def catch_all(path, predicate):
    return True


def executable(path, predicate):
    """Predicate is either true/yes/1 or false/no/0 (case-insensitive).

    This only works on Unix.

    """
    is_executable = (os.stat(path).st_mode & 0111) != 0
    return is_executable is what_we_want(predicate)


def fnmatch(path, predicate):
    """Match using the fnmatch module; always case-sensitive.
    """
    return _fnmatch.fnmatchcase(path, predicate)


def hashbang(path, predicate):
    """Match if the file starts with '#!'.
    """
    if not os.path.isfile(path):
        return False
    has_hashbang = (open(path).read(2) == '#!')
    return has_hashbang is what_we_want(predicate)


def isdir(path, predicate):
    return os.path.isdir(path) is what_we_want(predicate)


def isfile(path, predicate):
    return os.path.isfile(path) is what_we_want(predicate)


def mimetype(path, predicate):
    """Match against the resource's MIME type.
    """
    if not os.path.isfile(path):
        return False
    return predicate == mimetypes.guess_type(path)[0]


def rematch(path, predicate):
    """Match based on a regular expression.
    """
    return re.match(predicate, path) is not None


def svn_prop(path, predicate):
    """Match based on an arbitrary subversion property.

    Syntax is:

        svn:prop=foo

    This rule requires the svn command-line client.

    XXX: make this portable (use subprocess instead of command)

    """
    try:
        propname, expected = predicate.split('=',1)
    except ValueError:
        raise RuleError('bad predicate for svn_prop: %s' % predicate)

    command = "svn propget '%s' %s" % (propname, path)
    status, output = commands.getstatusoutput(command)
    if status > 0:
        raise RuleError(output)
    actual = output.strip()

    return expected == actual



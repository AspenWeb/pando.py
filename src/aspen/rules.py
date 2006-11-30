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

        >>> def rule(fp, predicate):
        >>>     some_condition = my_test(fp)
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

def executable(fp, predicate):
    """Predicate is either true/yes/1 or false/no/0 (case-insensitive).

    This only works on Unix.

    """
    is_executable = (os.stat(fp.name).st_mode & 0111) != 0
    return is_executable is what_we_want(predicate)


def fnmatch(fp, predicate):
    """Match using the fnmatch module; always case-sensitive.
    """
    return _fnmatch.fnmatchcase(fp.name, predicate)


def hashbang(fp, predicate):
    """Match if the file starts with '#!'.
    """
    has_hashbang = (fp.read(2) == '#!')
    return has_hashbang is what_we_want(predicate)


def mimetype(fp, predicate):
    """Match against the resource's MIME type.
    """
    return predicate == mimetypes.guess_type(fp.name)[0]


def rematch(fp, predicate):
    """Match based on a regular expression.
    """
    return re.match(predicate, fp.name) is not None


def svn_prop(fp, predicate):
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

    command = "svn propget '%s' %s" % (propname, fp.name)
    status, output = commands.getstatusoutput(command)
    if status > 0:
        raise RuleError(output)
    actual = output.strip()

    return expected == actual



"""Module for loading objects specified in colon notation.
"""
import string
from os.path import basename

from aspen.configuration.exceptions import ConfFileError


INITIAL = '_' + string.letters
INNER = INITIAL + string.digits
def is_valid_identifier(s):
    """Given a string of length > 0, return a boolean.

        >>> is_valid_identifier('.svn')
        False
        >>> is_valid_identifier('svn')
        True
        >>> is_valid_identifier('_svn')
        True
        >>> is_valid_identifier('__svn')
        True
        >>> is_valid_identifier('123')
        False
        >>> is_valid_identifier('r123')
        True

    """
    try:
        assert s[0] in INITIAL
        assert False not in [x in INNER for x in s]
        return True
    except AssertionError:
        return False


class ColonizeError(ConfFileError):
    pass

class ColonizeBadColonsError(ColonizeError): pass
class ColonizeBadObjectError(ColonizeError): pass
class ColonizeBadModuleError(ColonizeError): pass


def colonize(name, filename='n/a', lineno=-1):
    """Given a name in colon notation and some error helpers, return an object.

    The format of name is a subset of setuptools entry_point format: a
    dotted module name, followed by a colon and a dotted identifier naming
    an object within the module.

    """

    if name.count(':') != 1:
        msg = "'%s' is not valid colon notation" % name
        raise ColonizeBadColonsError(msg, filename, lineno)

    modname, objname = name.rsplit(':', 1) # no rsplit < Python 2.4

    for _name in modname.split('.'):
        if not is_valid_identifier(_name):
            msg = ( "'%s' is not valid colon notation: " % name
                  + "bad module name '%s'" % _name
                   )
            raise ColonizeBadModuleError(msg, filename, lineno)

    try:
        if '.' in modname:
            pkg, mod = modname.rsplit('.', 1)
            exec 'from %s import %s as obj' % (pkg, mod)
        else:
            exec 'import %s as obj' % modname
    except ImportError, err:
        newmsg = "%s [%s, line %s]" % (err.args[0], basename(filename), lineno)
        err.args = (newmsg,)
        raise # preserve the original traceback

    for _name in objname.split('.'):
        if not is_valid_identifier(_name):
            msg = ( "'%s' is not valid colon notation: " % name
                  + "bad object name '%s'" % _name
                   )
            raise ColonizeBadObjectError(msg, filename, lineno)
        try:
            obj = getattr(obj, _name)
        except AttributeError, err:
            newmsg = "%s [%s, line %s]" % ( err.args[0]
                                          , basename(filename)
                                          , lineno
                                           )
            err.args = (newmsg,)
            raise # preserve the original traceback

    return obj

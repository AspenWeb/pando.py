"""Module for loading objects specified in colon notation.
"""
from os.path import basename

from aspen import utils
from aspen.exceptions import ConfigError


class ColonizeError(ConfigError):
    pass

class ColonizeBadColonsError(ColonizeError): pass
class ColonizeBadObjectError(ColonizeError): pass
class ColonizeBadModuleError(ColonizeError): pass


def colonize(name, filename, lineno):
    """Given a name in colon notation and some error helpers, return an object.

    The format of name is a subset of setuptools entry_point format: a
    dotted module name, followed by a colon and a dotted identifier naming
    an object within the module.

    """

    if name.count(':') != 1:
        msg = "'%s' is not valid colon notation" % name
        raise ColonizeBadColonsError(msg, filename, lineno)

    #modname, objname = name.rsplit(':', 1) -- no rsplit < Python 2.4
    idx = name.rfind(":")
    modname = name[:idx]
    objname = name[idx+1:]

    for _name in modname.split('.'):
        if not utils.is_valid_identifier(_name):
            msg = ( "'%s' is not valid colon notation: " % name
                  + "bad module name '%s'" % _name
                   )
            raise ColonizeBadModuleError(msg, filename, lineno)

    try:
        exec 'import %s as obj' % modname
    except ImportError, err:
        newmsg = "%s [%s, line %s]" % (err.args[0], basename(filename), lineno)
        err.args = (newmsg,)
        raise # preserve the original traceback

    for _name in objname.split('.'):
        if not utils.is_valid_identifier(_name):
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

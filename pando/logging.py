"""Pando logging convenience wrappers"""

import sys
import logging


def log(*messages, **kw):
    """
    Make logging more convenient - use magic to get the __name__ of the calling module/function
    and log as it.

    'level' if present as a kwarg, is the level to log at.
    'upframes' if present as a kwarg, is how many frames up to look for the name.

    other kwargs are passed through to Logger.log()
    """
    level = kw.pop('level', logging.WARNING)
    upframes = kw.pop('upframes', 1)
    callerName = sys._getframe(upframes).f_globals.get('__name__', '<unknown>')
    logging.getLogger(callerName).log(level, *messages, **kw)


def log_dammit(*messages, **kw):
    """
    like log(), but critical instead of warning
    """
    kw['level'] = kw.get('level', logging.CRITICAL)
    kw['upframes'] = kw.get('upframes', 2)
    log(*messages, **kw)

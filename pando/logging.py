"""
pando.logging
+++++++++++++

Pando logging convenience wrappers

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import logging

LOGGING_THRESHOLD = 0

def log(*messages, **kw):
    """
    Make logging more convenient - use magic to get the __name__ of the calling module/function
    and log as it.

    'level' if present as a kwarg, is the level to log at.
    'upframes' if present as a kwarg, is how many frames up to look for the name.

    other kwargs are passed through to Logger.log()
    """
    level = kw.get('level', logging.WARNING)
    if 'level' in kw: del kw['level']
    upframes = kw.get('upframes', 1)
    if 'upframes' in kw: del kw['upframes']
    callerName = sys._getframe(upframes).f_globals.get('__name__', '<unknown>')
    logging.getLogger(callerName).log(level, *messages, **kw)

def log_dammit(*messages, **kw):
    """
    like log(), but critical instead of warning
    """
    kw['level'] = kw.get('level', logging.CRITICAL)
    kw['upframes'] = kw.get('upframes', 2)
    log(*messages, **kw)

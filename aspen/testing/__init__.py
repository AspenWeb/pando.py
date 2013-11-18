from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
from aspen import resources, sockets


CWD = os.getcwd()


def teardown():
    """Standard teardown function.

    - reset the current working directory
    - remove FSFIX = %{tempdir}/fsfix
    - reset Aspen's global state
    - clear out sys.path_importer_cache
    - clear out execution.extras

    """
    os.chdir(CWD)
    # Reset some process-global caches. Hrm ...
    resources.__cache__ = {}
    sockets.__sockets__ = {}
    sockets.__channels__ = {}
    sys.path_importer_cache = {} # see test_weird.py
    import aspen.execution
    aspen.execution.clear_changes()

teardown() # start clean

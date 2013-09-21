#from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import sys
from StringIO import StringIO

import aspen.logging
from aspen.logging import log, log_dammit


pat = re.compile("pid-\d* thread--?\d* \(MainThread\) (.*)")
def capture(*a, **kw):
    """This is a fixture function to capture log output.

    Positional and keyword arguments are passed through to a logging function
    with these exceptions, which are pulled out of kw before that is passed
    through to the logging function:

        func        the logging function to use, defaults to log
        threshold   where to set the logging threshold; it will be reset to its
                     previous value after the output of func is captured

    """
    func = kw.pop('func') if 'func' in kw else log
    try:
        __threshold__ = aspen.logging.LOGGING_THRESHOLD
        if 'threshold' in kw:
            aspen.logging.LOGGING_THRESHOLD = kw.pop('threshold')
        sys.stdout = StringIO()
        func(*a, **kw)
        output = sys.stdout.getvalue()
    finally:
        aspen.logging.LOGGING_THRESHOLD = __threshold__
        sys.stdout = sys.__stdout__
    return pat.findall(output)


def test_log_logs_something():
    actual = capture("oh heck", level=4)
    assert actual == ["oh heck"], actual

def test_log_logs_several_somethings():
    actual = capture("oh\nheck", u"what?", {}, [], None, level=4)
    assert actual == ["oh", "heck", "what?", "{}", "[]", "None"], actual

def test_log_dammit_works():
    actual = capture("yes\nrly", {}, [], None, threshold=1, func=log_dammit)
    assert actual == ["yes", "rly", "{}", "[]", "None"], actual

def test_logging_unicode_works():
    actual = capture("oh \u2614 heck", level=4)
    assert actual == ["oh \u2614 heck"], actual


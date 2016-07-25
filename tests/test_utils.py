from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pando.utils import to_rfc822
from datetime import datetime


def test_to_rfc822():
    expected = 'Thu, 01 Jan 1970 00:00:00 GMT'
    actual = to_rfc822(datetime(1970, 1, 1))
    assert actual == expected

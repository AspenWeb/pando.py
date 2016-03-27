from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from pytest import raises

from pando.utils import to_age, to_rfc822, utcnow
from datetime import datetime, timedelta


def test_to_age_barely_works():
    now = utcnow()
    actual = to_age(now, dt_now=now)
    assert actual == "in just a moment"

    wait = timedelta(seconds=0.5)
    actual = to_age(now - wait, dt_now=now)
    assert actual == "just a moment ago"

def test_to_age_fails():
    raises(ValueError, to_age, datetime.utcnow())

def test_to_age_formatting_works():
    now = utcnow()
    actual = to_age(now, fmt_future="Cheese, for %(age)s!", dt_now=now)
    assert actual == "Cheese, for just a moment!"

def test_to_rfc822():
    expected = 'Thu, 01 Jan 1970 00:00:00 GMT'
    actual = to_rfc822(datetime(1970, 1, 1))
    assert actual == expected

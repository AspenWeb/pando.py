from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def test_website_can_respond(harness):
    harness.www.mk(('index.html.spt', 'Greetings, program!'))
    assert harness.get('/').body == 'Greetings, program!'

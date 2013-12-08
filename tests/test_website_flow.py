from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def test_website_can_respond(harness):
    harness.fs.www.mk(('index.html.spt', 'Greetings, program!'))
    assert harness.client.GET().body == 'Greetings, program!'

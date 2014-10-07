from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def test_website_can_respond(harness):
    harness.fs.www.mk(('index.spt', '[---]\n[---] text/html\nGreetings, program!'))
    assert harness.client.GET().body == 'Greetings, program!'


def test_404_comes_out_404(harness):
    harness.fs.project.mk(('404.spt', '[---]\n[---] text/plain\nEep!'))
    assert harness.client.GET(raise_immediately=False).code == 404

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from aspen.website import Website


simple_error_spt = """
[---]
[---] text/plain via stdlib_format
{response.body}
"""


# Tests
# =====

def test_basic():
    website = Website()
    expected = os.getcwd()
    actual = website.www_root
    assert actual == expected

def test_resources_can_import_from_project_root(harness):
    harness.fs.project.mk(('foo.py', 'bar = "baz"'))
    assert harness.simple( "from foo import bar\n[---]\n[---]\nGreetings, %(bar)s!"
                         , 'index.html.spt'
                         , raise_immediately=False).body == "Greetings, baz!"

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from aspen import json
from aspen.renderers import Factory, Renderer


def test_a_custom_renderer(harness):
    class TestRenderer(Renderer):

        def compile(self, *a):
            return self.raw.upper()

        def render_content(self, context):
            d = dict((k, v) for k, v in self.__dict__.items() if k[0] != '_')
            return json.dumps(d)

    class TestFactory(Factory):
        Renderer = TestRenderer

        def compile_meta(self, configuration):
            return 'foobar'

    website = harness.website
    website.renderer_factories['lorem'] = TestFactory(website)

    r = harness.simple("[---]\n[---] text/html via lorem\nLorem ipsum")
    d = json.loads(r.body)
    assert d['meta'] == 'foobar'
    assert d['raw'] == 'Lorem ipsum'
    assert d['media_type'] == 'text/html'
    assert d['offset'] == 2
    assert d['compiled'] == 'LOREM IPSUM'

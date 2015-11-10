from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def test_website_can_respond(harness):
    response = harness.simple('[---]\n[---]\nGreetings, program!', 'index.html.spt')
    assert response.body == 'Greetings, program!'


def test_user_can_influence_request_context_via_algorithm_state(harness):
    def add_foo_to_context(request):
        return {'foo': 'bar'}
    harness.client.website.algorithm.insert_after('parse_environ_into_request', add_foo_to_context)
    assert harness.simple('[---]\n[---]\n%(foo)s', 'index.html.spt').body == 'bar'

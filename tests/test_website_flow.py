from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from aspen.website import Website
from aspen.testing.client import Client


@pytest.yield_fixture
def website():
    yield Website()

@pytest.yield_fixture
def client(website, mk):
    yield Client(website)

def test_website_can_respond(client):
    response = client.get('/')
    assert response.body == "Greetings, program!"

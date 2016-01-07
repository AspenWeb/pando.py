from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

import pytest
from aspen.testing import Harness, teardown


@pytest.yield_fixture
def sys_path_scrubber():
    before = set(sys.path)
    yield
    after = set(sys.path)
    for name in after - before:
        sys.path.remove(name)


@pytest.yield_fixture
def harness(sys_path_scrubber):
    harness = Harness()
    yield harness
    harness.teardown()


@pytest.yield_fixture
def django_client(harness):
    harness.fs.project.mk(
    ('aspen_django_urls.py', '''
from aspen.shims import django as shim
from django.conf.urls import patterns

urlpatterns = patterns('', (r'^', shim.view))
'''),
    ('aspen_django_settings.py', '''
SECRET_KEY = 'cheese'
ROOT_URLCONF = 'aspen_django_urls'
DEBUG = TEMPLATE_DEBUG = True

from aspen.shims import django as shim
ASPEN_REQUEST_PROCESSOR = shim.install()
'''))

    sys.path.insert(0, harness.fs.project.root)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'aspen_django_settings'

    try:
        import django
    except ImportError:
        raise pytest.skip.Exception
    else:
        from django.test.client import Client
        yield Client()
    finally:
        del os.environ['DJANGO_SETTINGS_MODULE']
        sys.path = sys.path[1:]


@pytest.yield_fixture
def flask_client(harness):
    try:
        import flask
    except ImportError:
        raise pytest.skip.Exception

    harness.fs.project.mk(
    ('aspen_flask_app.py', '''
import flask
from aspen.shims import flask as shim

app = flask.Flask(__name__)
app.debug = True
shim.install(app)
'''))
    sys.path.insert(0, harness.fs.project.root)
    from aspen_flask_app import app
    with app.test_client() as flask_client:
        yield flask_client
    sys.path = sys.path[1:]


def pytest_runtest_teardown():
    teardown()

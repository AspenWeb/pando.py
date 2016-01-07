import os, sys

def test_django_shim_is_importable():
    from aspen.shims import django as shim
    assert shim

def test_django_shim_basically_works(harness, DjangoClient):
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
'''),
    ('www/index.spt', '''
program = request.GET['program']
[-----] text/html
Greetings, {{program}}!
'''))
    sys.path.insert(0, harness.fs.project.root)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'aspen_django_settings'
    dc = DjangoClient()
    response = dc.request(QUERY_STRING='program=django')
    assert response.content == 'Greetings, django!\n'

def test_flask_shim_is_importable():
    from aspen.shims import flask as shim
    assert shim

def test_flask_shim_basically_works(harness, DjangoClient):
    harness.fs.project.mk(
    ('aspen_flask_app.py', '''
import flask
from aspen.shims import flask as shim

app = flask.Flask(__name__)
shim.install(app)
'''),
    ('www/index.spt', '''
program = request.args['program']
[-----] text/html
Greetings, {{program}}!
'''))
    sys.path.insert(0, harness.fs.project.root)
    from aspen_flask_app import app
    app.debug = True
    with app.test_client() as client:
        response = client.get('/?program=flask')
    assert response.get_data() == 'Greetings, flask!'

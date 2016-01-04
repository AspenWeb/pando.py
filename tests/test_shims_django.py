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

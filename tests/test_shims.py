def test_django_shim_is_importable():
    from aspen.shims import django as shim
    assert shim

def test_django_shim_basically_works(harness, django_client):
    harness.fs.project.mk(('www/index.spt', '''
program = request.GET['program']
[-----] text/html
Greetings, {{program}}!
'''))
    response = django_client.request(QUERY_STRING='program=django')
    assert response.content == 'Greetings, django!\n'

def test_flask_shim_is_importable():
    from aspen.shims import flask as shim
    assert shim

def test_flask_shim_basically_works(harness, flask_client):
    harness.fs.project.mk(('www/index.spt', '''
program = request.args['program']
[-----] text/html
Greetings, {{program}}!
'''))
    response = flask_client.get('/?program=flask')
    assert response.get_data() == 'Greetings, flask!'

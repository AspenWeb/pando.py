
def test_test_client_handles_body(harness):
    harness.fs.www.mk(('foo.spt', '''
    [---]
    bar = request.body['bar']
    [---] text/html via stdlib_format
    {bar}
    '''))
    harness.client.POST('/foo', data={'bar': '42'})

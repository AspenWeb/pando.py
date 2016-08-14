from pando.testing.client import FileUpload


def test_test_client_handles_body(harness):
    harness.fs.www.mk(('foo.spt', '''
    [---]
    bar = request.body['bar']
    [---] text/html via stdlib_format
    {bar}'''))
    response = harness.client.POST('/foo', data={b'bar': b'42'})
    assert response.body == b'42'

def test_test_client_handles_file_upload(harness):
    harness.fs.www.mk(('foo.spt', '''
    [---]
    bar = request.body['bar']
    bar.value = bar.value.decode()
    [---] text/plain via stdlib_format
    {bar.filename}
    {bar.type}
    {bar.value}'''))
    file_upload = FileUpload( data=b'Greetings, program!'
                            , filename=b'greetings.txt'
                             )
    response = harness.client.POST('/foo', data={b'bar': file_upload})
    assert response.body == b'greetings.txt\ntext/plain\nGreetings, program!'

def test_test_client_can_have_file_upload_content_type_overriden(harness):
    harness.fs.www.mk(('foo.spt', '''
    [---]
    bar = request.body['bar']
    [---] text/plain via stdlib_format
    {bar.type}'''))
    file_upload = FileUpload( data=b'Greetings, program!'
                            , filename=b'greetings.txt'
                            , content_type=b'something/else'
                             )
    response = harness.client.POST('/foo', data={b'bar': file_upload})
    assert response.body == b'something/else'

import wsgiservice

def test_mount():
    @wsgiservice.mount('/{id}')
    class Document(wsgiservice.Resource):
        pass
    assert Document.__name__ == 'Document'
    assert Document._path == '/{id}'

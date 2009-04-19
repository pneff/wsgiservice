import wsgiservice

def test_mount():
    @wsgiservice.mount('/{id}')
    class Document(wsgiservice.Resource):
        pass
    assert Document.__name__ == 'Document'
    assert Document._path == '/{id}'

def test_validate_resource():
    @wsgiservice.validate('id', re=r'[-0-9a-zA-Z]{36}', doc='Document ID, must be a valid UUID.')
    class User(wsgiservice.Resource):
        pass
    print User._validations
    assert User.__name__ == 'User'
    assert User._validations['id'] == {'re': r'[-0-9a-zA-Z]{36}',
        'doc': 'Document ID, must be a valid UUID.'}

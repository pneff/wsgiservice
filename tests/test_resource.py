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

def test_validate_method():
    class User(wsgiservice.Resource):
        @wsgiservice.validate('password', doc="User's password")
        @wsgiservice.validate('username', re='[a-z]+')
        def PUT(self, password):
            pass
    print User.PUT._validations
    assert User.PUT.__name__ == 'PUT'
    assert User.PUT._validations['password'] == {'re': None, 'doc': "User's password"}
    assert User.PUT._validations['username'] == {'re': '[a-z]+', 'doc': None}

def test_serialisation_bool():
    class User(wsgiservice.Resource):
        pass
    u = User(None, None, None)
    s = u.to_text_xml(True)
    print s
    assert s == '<response>true</response>'

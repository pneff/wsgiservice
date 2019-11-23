# -*- coding: utf-8 -*-
import json

import six

import webob
import wsgiservice


def test_mount():
    """mount decorator adds the path as an attribute _path."""

    @wsgiservice.mount('/{id}')
    class Document(wsgiservice.Resource):
        pass

    assert Document.__name__ == 'Document'
    assert Document._path == '/{id}'


def test_validate_resource():
    """validate decorator adds rules to the _validations attribute list."""

    @wsgiservice.validate('id', re=r'[-0-9a-zA-Z]{36}',
        doc='Document ID, must be a valid UUID.')
    class User(wsgiservice.Resource):
        pass

    print(User._validations)
    assert User.__name__ == 'User'
    assert User._validations['id'] == {'re': r'[-0-9a-zA-Z]{36}',
        'convert': None, 'doc': 'Document ID, must be a valid UUID.'}


def test_validate_method():
    """validate decorator adds rules to the _validations attribute list."""

    class User(wsgiservice.Resource):

        @wsgiservice.validate('password', doc="User's password")
        @wsgiservice.validate('username', re='[a-z]+')
        def PUT(self, password):
            pass

    print(User.PUT._validations)
    assert User.PUT.__name__ == 'PUT'
    assert User.PUT._validations['password'] == {'re': None,
        'convert': None, 'doc': "User's password"}
    assert User.PUT._validations['username'] == {'re': '[a-z]+',
        'convert': None, 'doc': None}


def test_default_value():
    """Request parameters can have default values."""

    class User(wsgiservice.Resource):

        def GET(self, foo, bar, id=5):
            return {'id': id, 'bar': bar, 'foo': foo}

    req = webob.Request.blank('/?foo=baz1&bar=baz2',
        headers={'Accept': 'application/json'})
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    obj = json.loads(res.body)
    print(obj)
    assert obj == {'id': 5, 'foo': 'baz1', 'bar': 'baz2'}


def test_default_value_overwrite():
    """Parameters with default values can be overwritten in the request."""

    class User(wsgiservice.Resource):

        def GET(self, foo, id=5):
            return {'id': id, 'foo': foo}

    req = webob.Request.blank('/?id=8&foo=bar',
        headers={'Accept': 'application/json'})
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    obj = json.loads(res.body)
    print(obj)
    assert obj == {'id': '8', 'foo': 'bar'}


def test_default_value_validate_novalue():
    """Default parameters are validated correctly when not passed in."""

    class User(wsgiservice.Resource):

        @wsgiservice.validate('id', doc='Foo')
        def GET(self, foo, id=5):
            return {'id': id, 'foo': foo}

    req = webob.Request.blank('/?foo=bar',
        headers={'Accept': 'application/json'})
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    obj = json.loads(res.body)
    print(obj)
    assert obj == {'id': 5, 'foo': 'bar'}


def test_default_value_validate():
    """Default parameters are validated correctly when passed in."""

    class User(wsgiservice.Resource):

        @wsgiservice.validate('id', doc='Foo')
        def GET(self, foo, id=5):
            return {'id': id, 'foo': foo}

    req = webob.Request.blank('/?id=&foo=bar',
        headers={'Accept': 'application/json'})
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 400
    obj = json.loads(res.body)
    print(obj)
    assert obj == {"error": "Value for id must not be empty."}


def test_convert_params():
    """Convert parameters using the function given."""

    class User(wsgiservice.Resource):
        @wsgiservice.validate('foo', convert=int)
        @wsgiservice.validate('bar', convert=repr)
        def GET(self, foo, bar):
            return {'foo': foo, 'foo_type': str(type(foo)),
                    'bar': bar, 'bar_type': str(type(bar))}

    req = webob.Request.blank('/?foo=193&bar=testing',
        headers={'Accept': 'application/json'})
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 200
    obj = json.loads(res.body)
    assert obj['foo'] == 193
    if six.PY2:
        assert obj['bar'] == "u'testing'"
        assert obj['foo_type'] == "<type 'int'>"
        assert obj['bar_type'] == "<type 'str'>"
    else:
        assert obj['bar'] == "'testing'"
        assert obj['foo_type'] == "<class 'int'>"
        assert obj['bar_type'] == "<class 'str'>"


def test_latin1_submit():
    """Don't access request.POST magically if method doesn't expect params.

    This way if a web service wants to handle non-expected data (WebOb only
    allows UTF-8), it can do so manually inside the method.
    """

    class User(wsgiservice.Resource):
        def POST(self):
            return {'body': repr(self.request.body)}

    req = webob.Request.blank('/test', {'REQUEST_METHOD': 'POST'},
        headers={'Accept': 'application/json',
                 'Content-Type': 'application/x-www-form-urlencoded'})
    req.body = u'Fühler'.encode('latin1')
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 200
    obj = json.loads(res.body)
    if six.PY2:
        assert obj == {'body': "'F\\xfchler'"}
    else:
        assert obj == {'body': "b'F\\xfchler'"}


def test_convert_params_validate():
    """Use the conversion function to validate as well."""

    class User(wsgiservice.Resource):
        @wsgiservice.validate('a', convert=int)
        def GET(self, a):
            return {'a': a}

    req = webob.Request.blank('/?a=b', headers={'Accept': 'application/json'})
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 400
    obj = json.loads(res.body)
    assert obj == {"error": "a value b does not validate."}


def test_ignore_robotstxt():
    """Ignore the robots.txt resource on root resources."""

    class Dummy(wsgiservice.Resource):
        _path = '/{id}'

        def GET(self, id):
            return id

    req = webob.Request.blank('/robots.txt')
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 404


def test_ignore_favicon():
    """Ignore the favicon.ico resource on root resources."""

    class Dummy(wsgiservice.Resource):
        _path = '/{id}'

        def GET(self, id):
            return id

    req = webob.Request.blank('/favicon.ico')
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 404


def test_ignore_favicon_overwrite():
    """Don't ignore favicon.ico when IGNORED_PATHS is empty."""

    class Dummy(wsgiservice.Resource):
        _path = '/{id}'
        IGNORED_PATHS = ()

        def GET(self, id):
            return id

    req = webob.Request.blank('/favicon.ico')
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 200


def test_ignore_favicon_not_root():
    """Don't ignore favicon.ico on non-root requests."""

    class Dummy(wsgiservice.Resource):
        _path = '/foo/{id}'

        def GET(self, id):
            return id

    req = webob.Request.blank('/foo/favicon.ico')
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 200


def test_ignore_favicon_query_param():
    """Don't ignore favicon.ico with query parameters"""

    class Dummy(wsgiservice.Resource):
        _path = '/{id}'

        def GET(self, id):
            return id

    req = webob.Request.blank('/favicon.ico?x=1')
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 200


def test_ignore_favicon_post():
    """Only ignore favicon.ico for GET requests."""

    class Dummy(wsgiservice.Resource):
        _path = '/{id}'

        def POST(self, id):
            return id

    req = webob.Request.blank('/favicon.ico?', {'REQUEST_METHOD': 'POST'})
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 200


def test_default_mimetype():
    """Use the first item of EXTENSION_MAP as the default."""

    class Dummy(wsgiservice.Resource):
        EXTENSION_MAP = [
            ('.txt', 'text/plain'),
            ('.xml', 'text/xml'),
        ]
        _path = '/status'

        def GET(self, id):
            return 'OK'

        def to_text_plain(self, raw):
            return raw

    req = webob.Request.blank('/status')
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.headers['Content-Type'] == 'text/plain; charset=UTF-8'


def test_invalid_accept():
    """Again use the first item of EXTENSION_MAP as the default if the
    `Accept` header has an unknown value.
    """
    class Dummy(wsgiservice.Resource):
        _path = '/test'

        def GET(self, id):
            return {'status': 'success'}

    req = webob.Request.blank('/test', headers={'Accept': 'text/json'})
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.headers['Content-Type'] == 'text/xml; charset=UTF-8'


def test_raise_404():
    """Use NotFoundResource when a 404 response is raised."""

    class Dummy(wsgiservice.Resource):
        _path = '/test'
        def GET(self):
            wsgiservice.raise_404(self)

    req = webob.Request.blank('/test')
    res = webob.Response()
    usr = Dummy(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.headers['Content-Type'] == 'text/xml; charset=UTF-8'

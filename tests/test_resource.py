# -*- coding: utf-8 -*-
try:
    import json
except ImportError:
    import simplejson as json
import webob
import wsgiservice


def test_validate_method():
    """validate decorator adds rules to the _validations attribute list."""

    class User(wsgiservice.Resource):

        @wsgiservice.validate('password', doc="User's password")
        @wsgiservice.validate('username', re='[a-z]+')
        def PUT(self, password):
            pass

    print User.PUT._validations
    assert User.PUT.__name__ == 'PUT'
    assert User.PUT._validations['password'] == {'re': None,
        'doc': "User's password"}
    assert User.PUT._validations['username'] == {'re': '[a-z]+', 'doc': None}


def test_serialisation_bool():
    """XML serialization uses the lower-case string value for booleans."""

    class User(wsgiservice.Resource):
        pass

    u = User(None, None, None)
    s = u.to_text_xml(True)
    print s
    assert s == '<response>true</response>'


def test_serialisation_unicode():
    """Unicode strings are converted to UTF-8."""

    class User(wsgiservice.Resource):
        pass

    u = User(None, None, None)
    s = u.to_text_xml({'test': u'gfröhrli'})
    print s
    assert s == '<response><test>gfröhrli</test></response>'


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
    print res
    obj = json.loads(res.body)
    print obj
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
    print res
    obj = json.loads(res.body)
    print obj
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
    print res
    obj = json.loads(res.body)
    print obj
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
    print res
    assert res.status_int == 400
    obj = json.loads(res.body)
    print obj
    assert obj == {"error": "Value for id must not be empty."}


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
    print res
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
    print res
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
    print res
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
    print res
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
    print res
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
    print res
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
    print res
    assert res.headers['Content-Type'] == 'text/plain; charset=UTF-8'

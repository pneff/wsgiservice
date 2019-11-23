# -*- coding: utf-8 -*-
"""Tests for handling of JSON request data."""
import json

import webob
import wsgiservice


def test_default_value():
    """Request parameters can have default values."""

    class User(wsgiservice.Resource):

        def POST(self, foo, bar, id=5):
            return {'id': id, 'bar': bar, 'foo': foo}

    data = {'foo': 'baz1', 'bar': 'baz2'}
    req = create_blank_request(
        '/', headers={
            'Accept': 'application/json', 'Content-Type': 'application/json'},
        method='POST', body=json.dumps(data))
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

        def POST(self, foo, id=5):
            return {'id': id, 'foo': foo}

    data = {'id': '8', 'foo': 'bar'}
    req = create_blank_request('/', headers={'Accept': 'application/json',
                                            'Content-Type': 'application/json'},
                              method='POST', body=json.dumps(data))
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
        def POST(self, foo, id=5):
            return {'id': id, 'foo': foo}

    data = {'foo': 'bar'}
    req = create_blank_request('/', headers={'Accept': 'application/json',
                                            'Content-Type': 'application/json'},
                              method='POST', body=json.dumps(data))
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
        def POST(self, foo, id=5):
            return {'id': id, 'foo': foo}

    data = {'foo': 'bar', 'id': None}
    req = create_blank_request('/', headers={'Accept': 'application/json',
                                            'Content-Type': 'application/json'},
                              method='POST', body=json.dumps(data))
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 400
    obj = json.loads(res.body)
    print(obj)
    assert obj == {"error": "Value for id must not be empty."}


def test_validate_empty():
    """Empty strings are not accepted as values for default validation"""

    class User(wsgiservice.Resource):

        @wsgiservice.validate('id', doc='Foo')
        def POST(self, foo, id=5):
            return {'id': id, 'foo': foo}

    data = {'foo': 'bar', 'id': ''}
    req = create_blank_request('/', headers={'Accept': 'application/json',
                                            'Content-Type': 'application/json'},
                              method='POST', body=json.dumps(data))
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
        @wsgiservice.validate('baz', convert=int)
        def POST(self, foo, bar, baz):
            return {'foo': foo, 'foo_type': str(type(foo)),
                    'bar': bar, 'bar_type': str(type(bar)),
                    'baz': baz, 'baz_type': str(type(baz))}

    data = {'foo': '193', 'bar': 'testing', 'baz': 212}
    req = create_blank_request('/', headers={'Accept': 'application/json',
                                            'Content-Type': 'application/json'},
                              method='POST', body=json.dumps(data))
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 200
    obj = json.loads(res.body)
    assert obj['foo'] == 193
    assert obj['foo_type'] == "<class 'int'>"
    assert obj['bar'] == "'testing'"
    assert obj['bar_type'] == "<class 'str'>"
    assert obj['baz'] == 212
    assert obj['baz_type'] == "<class 'int'>"


def test_convert_params_validate():
    """Use the conversion function to validate as well."""

    class User(wsgiservice.Resource):
        @wsgiservice.validate('a', convert=int)
        def POST(self, a):
            return {'a': a}

    data = {'a': 'b'}
    req = create_blank_request('/', headers={'Accept': 'application/json',
                                            'Content-Type': 'application/json'},
                              method='POST', body=json.dumps(data))
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 400
    obj = json.loads(res.body)
    assert obj == {"error": "a value b does not validate."}


def test_raise_400_invalid_json():
    """Validate the JSON that's passed in."""

    class User(wsgiservice.Resource):
        def POST(self):
            return self.data

    req = create_blank_request('/', headers={'Accept': 'application/json',
                                            'Content-Type': 'application/json'},
                              method='POST', body='{"foo":')
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 400
    obj = json.loads(res.body)
    assert obj == {"error": "Invalid JSON content data"}


def test_accept_non_dict():
    """Input data are not necessarily dictionaries.

    Make sure nothing breaks, but the `data` won't contain those values.
    """

    class User(wsgiservice.Resource):
        def POST(self):
            return self.data

    req = create_blank_request('/', headers={'Accept': 'application/json',
                                            'Content-Type': 'application/json'},
                              method='POST', body=b'123')
    res = webob.Response()
    usr = User(request=req, response=res, path_params={})
    res = usr()
    print(res)
    assert res.status_int == 200
    obj = json.loads(res.body)
    assert obj == {}


def create_blank_request(*args, **kwargs):
    """Create a blank test request.

    Will convert the body to byte.
    """
    if isinstance(kwargs.get('body'), str):
        kwargs['body'] = kwargs['body'].encode('utf8')
    return webob.Request.blank(*args, **kwargs)

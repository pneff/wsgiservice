import mox
import StringIO
import time
import wsgiservice
import wsgiservice.application
import wsgiservice.exceptions

def test_getapp():
    app = wsgiservice.get_app(globals())
    print app
    assert isinstance(app, wsgiservice.application.Application)
    assert len(app._resources) == 4
    resources = (Resource1, Resource2, Resource3, Resource4)
    assert app._resources[0] in resources
    assert app._resources[1] in resources
    assert app._resources[2] in resources
    assert app._resources[3] in resources

def test_app_handle_404():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/foo'}
    res = app._handle_request(env)
    print res
    assert res.status == '404 Not Found'
    assert str(res) == '<response><error>not found</error></response>'

def test_app_handle_method_not_allowed():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res2', 'REQUEST_METHOD': 'GET'}
    res = app._handle_request(env)
    print res
    assert res.status == '405 Method Not Allowed'
    assert str(res) == '<response><error>Invalid method on resource</error></response>'
    assert res._headers['Allow'] == 'POST, PUT'

def test_app_get_simple():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res1/theid', 'REQUEST_METHOD': 'GET',
        'wsgi.input': StringIO.StringIO('foo=42&baz=foobar')}
    res = app._handle_request(env)
    print res
    assert res.status == '200 OK'
    assert str(res) == "<response>GET was called with request &lt;class 'wsgiservice.objects.Request'&gt;, id theid, foo None</response>"

def test_app_post_simple():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res1/theid', 'REQUEST_METHOD': 'POST',
        'wsgi.input': StringIO.StringIO('foo=42&baz=foobar')}
    res = app._handle_request(env)
    print res
    assert res.status == '200 OK'
    assert str(res) == "<response>POST was called with request &lt;class 'wsgiservice.objects.Request'&gt;, id theid, foo 42</response>"

def test_app_wsgi():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res1/theid.json', 'REQUEST_METHOD': 'GET',
        'wsgi.input': ''}
    start_response = mox.MockAnything()
    start_response('200 OK', [('Content-Type', 'application/json; charset=UTF-8')])
    mox.Replay(start_response)
    res = app(env, start_response)
    print res
    mox.Verify(start_response)
    assert res == '"GET was called with request <class \'wsgiservice.objects.Request\'>, id theid, foo None"'

def test_validation_method():
    app = wsgiservice.get_app(globals())
    inst = Resource1()
    app._validate_param(inst.GET, 'foo', '9')

def test_validation_class():
    app = wsgiservice.get_app(globals())
    inst = Resource1()
    app._validate_param(inst.GET, 'id', 'anyid')

def test_validation_with_re_none_value():
    app = wsgiservice.get_app(globals())
    inst = Resource1()
    try:
        app._validate_param(inst.GET, 'id', None)
    except wsgiservice.exceptions.ValidationException, e:
        print e
        assert str(e) == 'Value for id must not be empty.'
    else:
        assert False, "Expected an exception!"

def test_validation_with_re_mismatch():
    app = wsgiservice.get_app(globals())
    inst = Resource1()
    try:
        app._validate_param(inst.GET, 'id', 'fo')
    except wsgiservice.exceptions.ValidationException, e:
        print e
        assert str(e) == 'id value fo does not validate.'
    else:
        assert False, "Expected an exception!"

def test_validation_with_re_mismatch_toolong():
    app = wsgiservice.get_app(globals())
    inst = Resource1()
    try:
        app._validate_param(inst.GET, 'id', 'fooobarrr')
    except wsgiservice.exceptions.ValidationException, e:
        print e
        assert str(e) == 'id value fooobarrr does not validate.'
    else:
        assert False, "Expected an exception!"

def test_with_expires():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res3', 'REQUEST_METHOD': 'GET',
        'wsgi.input': StringIO.StringIO('')}
    res = app._handle_request(env)
    print res._headers
    assert res._headers['Cache-Control'] == 'max-age=138'

def test_with_expires_calculations():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res4', 'REQUEST_METHOD': 'GET',
        'wsgi.input': StringIO.StringIO('')}
    res = app._handle_request(env)
    print res._headers
    assert res._headers['Cache-Control'] == 'max-age=138'
    assert res._headers['Expires'] == 'Mon, 20 Apr 2009 16:55:45 GMT'

def test_with_expires_calculations_double_wrapped():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res4', 'REQUEST_METHOD': 'POST',
        'wsgi.input': StringIO.StringIO('')}
    res = app._handle_request(env)
    print res._headers
    assert res._headers['Cache-Control'] == 'max-age=139'
    assert res._headers['Expires'] == 'Mon, 20 Apr 2009 16:55:46 GMT'


class Resource1(wsgiservice.Resource):
    _path = '/res1/{id}'
    _validations = {'id': {'re': '[a-z]{5}'}}
    def GET(self, request, id, foo):
        return 'GET was called with request {0}, id {1}, foo {2}'.format(
            type(request), id, foo)
    def POST(self, request, id, foo):
        return 'POST was called with request {0}, id {1}, foo {2}'.format(
            type(request), id, foo)
    POST._validations = {'foo': {'re': '[0-9]+'}}

class Resource2(wsgiservice.Resource):
    _path = '/res2'
    def POST(self):
        pass
    def PUT(self):
        pass

class Resource3(wsgiservice.Resource):
    _path = '/res3'
    @wsgiservice.expires(138)
    def GET(self, id):
        return "Called with id: {0}".format(id)

class Resource4(wsgiservice.Resource):
    _path = '/res4'
    @wsgiservice.expires(138, lambda: time.gmtime(1240250007))
    def GET(self, id):
        return "Called with id: {0}".format(id)

    @wsgiservice.expires(139, lambda: time.gmtime(1240250007))
    @wsgiservice.expires(138, lambda: time.gmtime(1240250007))
    def POST(self, id):
        return "POST Called with id: {0}".format(id)

import StringIO
import wsgiservice
import wsgiservice.application

def test_getapp():
    app = wsgiservice.get_app(globals())
    print app
    assert isinstance(app, wsgiservice.application.Application)
    assert len(app._resources) == 2
    assert app._resources[0] is Resource1
    assert app._resources[1] is Resource2

def test_app_handle_404():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/foo'}
    res = app._handle_request(env)
    print res
    assert res.status == '404 Not Found'
    assert str(res) == '<error>not found</error>'

def test_app_handle_method_not_allowed():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res2', 'REQUEST_METHOD': 'GET'}
    res = app._handle_request(env)
    print res
    assert res.status == '405 Method Not Allowed'
    assert str(res) == '<error>Invalid method on resource</error>'
    assert res._headers['Allow'] == 'POST, PUT'

def test_app_get_simple():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res1/theid', 'REQUEST_METHOD': 'GET',
        'wsgi.input': StringIO.StringIO('foo=bar&baz=foobar')}
    res = app._handle_request(env)
    print res
    assert res.status == '200 OK'
    assert str(res) == "GET was called with request &lt;class 'wsgiservice.objects.Request'&gt;, id theid, foo None"

def test_app_post_simple():
    app = wsgiservice.get_app(globals())
    env = {'PATH_INFO': '/res1/theid', 'REQUEST_METHOD': 'POST',
        'wsgi.input': StringIO.StringIO('foo=bar&baz=foobar')}
    res = app._handle_request(env)
    print res
    assert res.status == '200 OK'
    assert str(res) == "POST was called with request &lt;class 'wsgiservice.objects.Request'&gt;, id theid, foo bar"


class Resource1(wsgiservice.Resource):
    _path = '/res1/{id}'
    def GET(self, request, id, foo):
        return 'GET was called with request {0}, id {1}, foo {2}'.format(
            type(request), id, foo)
    def POST(self, request, id, foo):
        return 'POST was called with request {0}, id {1}, foo {2}'.format(
            type(request), id, foo)

class Resource2(wsgiservice.Resource):
    _path = '/res2'
    def POST(self):
        pass
    def PUT(self):
        pass

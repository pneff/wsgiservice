import StringIO
import wsgiservice

def test_request_post():
    env = {
        'REQUEST_METHOD': 'POST',
        'wsgi.input': StringIO.StringIO('foo=bar&baz=foobar')
    }
    req = wsgiservice.Request(env)
    print req.POST
    assert req.POST['foo'] == 'bar'
    assert req.POST['baz'] == 'foobar'

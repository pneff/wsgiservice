import wsgiservice

def test_init():
    env = { 'HTTP_ACCEPT': '*/*' }
    r = wsgiservice.Response({'foo': 'bar'}, env)
    print r._headers
    assert r._headers['Content-Type'] == 'text/xml'
    assert r.headers[0] == ('Content-Type', 'text/xml')
    assert str(r) == '<foo>bar</foo>'

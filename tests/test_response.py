import wsgiservice

def test_init():
    env = { 'HTTP_ACCEPT': '*/*' }
    r = wsgiservice.Response({'foo': 'bar'}, env)
    print r._headers
    assert r._headers['Content-Type'] == 'text/xml'
    assert r.headers[0] == ('Content-Type', 'text/xml')
    assert str(r) == '<foo>bar</foo>'

def test_get_xml_list():
    env = { 'HTTP_ACCEPT': '*/*' }
    r = wsgiservice.Response(['xy', 'foo'], env)
    print str(r)
    assert str(r) == '<0>xy</0><1>foo</1>'

def test_init_extension():
    env = { 'HTTP_ACCEPT': 'text/xml' }
    r = wsgiservice.Response({'foo': 'bar'}, env, extension='.json')
    print r._headers
    assert r._headers['Content-Type'] == 'application/json'
    assert r.headers[0] == ('Content-Type', 'application/json')
    print str(r)
    assert str(r) == '{"foo": "bar"}'

def test_convert_from_method():
    def GET():
        return ['foo']
    GET.to_text_xml = lambda res: '<myxml/>'
    env = { 'HTTP_ACCEPT': '*/*' }
    r = wsgiservice.Response({'foo': 'bar'}, env, method=GET)
    print str(r)
    assert str(r) == '<myxml/>'

def test_status():
    env = {}
    r = wsgiservice.Response('foo', env, status=405)
    print r.status
    assert r.status == '405 Method Not Allowed'

def test_add_headers():
    env = {}
    r = wsgiservice.Response('foo', env, headers={'X-Test': 'True'})
    print r._headers
    assert len(r._headers) == 2
    assert r._headers['Content-Type'] == 'text/xml'
    assert r._headers['X-Test'] == 'True'
    assert r.headers[0] == ('Content-Type', 'text/xml')
    assert r.headers[1] == ('X-Test', 'True')

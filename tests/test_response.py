import wsgiservice

def test_init():
    env = { 'HTTP_ACCEPT': '*/*' }
    r = wsgiservice.Response({'foo': 'bar'}, env)
    print r._headers
    assert r._headers['Content-Type'] == 'text/xml; charset=UTF-8'
    assert r._headers['Vary'] == 'Accept'
    print str(r)
    assert str(r) == '<response><foo>bar</foo></response>'

def test_get_xml_list():
    env = { 'HTTP_ACCEPT': '*/*' }
    r = wsgiservice.Response(['xy', 'foo'], env)
    print str(r)
    assert str(r) == '<response><0>xy</0><1>foo</1></response>'

def test_init_extension():
    env = { 'HTTP_ACCEPT': 'text/xml' }
    r = wsgiservice.Response({'foo': 'bar'}, env, extension='.json')
    print r._headers
    assert r._headers['Content-Type'] == 'application/json; charset=UTF-8'
    assert not 'Vary' in r._headers
    assert r.headers[0] == ('Content-Type', 'application/json; charset=UTF-8')
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

def test_convert_root_tag_none():
    def GET():
        return 'OK'
    GET.text_xml_root = None
    env = {}
    r = wsgiservice.Response(GET(), env, method=GET)
    print str(r)
    assert str(r) == 'OK'

def test_convert_root_tag_from_method():
    def GET():
        return ['foo']
    GET.text_xml_root = 'output'
    env = {}
    r = wsgiservice.Response(GET(), env, method=GET)
    print str(r)
    assert str(r) == '<output><0>foo</0></output>'

def test_convert_root_tag_from_class():
    class MyResource(object):
        text_xml_root = 'foobar'
        def GET():
            return 'OK'
    env = {}
    r = wsgiservice.Response('OK', env, resource=MyResource(),
        method=MyResource.GET)
    print str(r)
    assert str(r) == '<foobar>OK</foobar>'

def test_status():
    env = {}
    r = wsgiservice.Response('foo', env, status=405)
    print r.status
    assert r.status == '405 Method Not Allowed'

def test_add_headers():
    env = {}
    r = wsgiservice.Response('foo', env, headers={'X-Test': 'True'})
    print r._headers
    print r.headers
    assert len(r._headers) == 3
    assert r._headers['Content-Type'] == 'text/xml; charset=UTF-8'
    assert r._headers['X-Test'] == 'True'
    assert r._headers['Vary'] == 'Accept'
    assert r.headers[0] == ('Vary', 'Accept')
    assert r.headers[1] == ('Content-Type', 'text/xml; charset=UTF-8')
    assert r.headers[2] == ('X-Test', 'True')

def test_add_headers_vary():
    env = {}
    r = wsgiservice.Response('foo', env, headers={'Vary': 'Accept-Language'})
    print r._headers
    assert len(r._headers) == 2
    assert r._headers['Content-Type'] == 'text/xml; charset=UTF-8'
    assert r._headers['Vary'] == 'Accept-Language, Accept'

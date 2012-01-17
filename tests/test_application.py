import mox
import StringIO
import time
from datetime import timedelta
from webob import Request
import wsgiservice
import wsgiservice.application
import wsgiservice.exceptions


def test_getapp():
    """get_app returns a list of resources from the dictionary."""
    app = wsgiservice.get_app(globals())
    print app
    print app._resources
    assert isinstance(app, wsgiservice.application.Application)
    assert len(app._resources) == 7
    resources = (Resource1, Resource2, Resource3, Resource4, Resource5,
        Resource6)
    assert app._resources[0] in resources
    assert app._resources[1] in resources
    assert app._resources[2] in resources
    assert app._resources[3] in resources
    assert app._resources[4] in resources
    assert app._resources[5] in resources


def test_app_handle_404():
    """Application returns a 404 status code if no resource is found."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/foo', {'HTTP_ACCEPT': 'text/xml'})
    res = app._handle_request(req)
    print res
    assert res.status == '404 Not Found'
    assert res.body == '<response><error>' \
        'The requested resource does not exist.</error></response>'
    assert res.headers['Content-Type'] == 'text/xml; charset=UTF-8'


def test_app_handle_method_not_allowed():
    """Application returns 405 for known but unimplemented methods."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res2', {'REQUEST_METHOD': 'GET'})
    res = app._handle_request(req)
    print res
    assert res.status == '405 Method Not Allowed'
    assert res.body == ''
    assert res._headers['Allow'] == 'OPTIONS, POST, PUT'


def test_app_handle_method_not_known():
    """Application returns 501 for unknown and unimplemented methods."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res2', {'REQUEST_METHOD': 'PATCH'})
    res = app._handle_request(req)
    print res
    assert res.status == '501 Not Implemented'
    assert res.body == ''
    assert res._headers['Allow'] == 'OPTIONS, POST, PUT'


def test_app_handle_response_201_abs():
    """raise_201 used the location header directly if it is absolute."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res2', {'REQUEST_METHOD': 'POST'})
    res = app._handle_request(req)
    print res
    assert res.status == '201 Created'
    assert res.body == ''
    assert res.location == '/res2/test'


def test_app_handle_response_201_rel():
    """raise_201 adds relative location header to the current request path."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res2', {'REQUEST_METHOD': 'PUT'})
    res = app._handle_request(req)
    print res
    assert res.status == '201 Created'
    assert res.body == ''
    assert res.location == '/res2/foo'


def test_app_handle_response_201_ext():
    """raise_201 ignores extension in the current path."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res2.json', {'REQUEST_METHOD': 'PUT'})
    res = app._handle_request(req)
    print res
    assert res.status == '201 Created'
    assert res.body == ''
    assert res.location == '/res2/foo'


def test_app_handle_options():
    """Resource provides a good default for the OPTIONS method."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res2', {'REQUEST_METHOD': 'OPTIONS'})
    res = app._handle_request(req)
    print res
    assert res.status == '200 OK'
    assert res._headers['Allow'] == 'OPTIONS, POST, PUT'


def test_app_get_simple():
    """Application handles GET request and ignored POST data in that case."""
    app = wsgiservice.get_app(globals())
    body = 'foo=42&baz=foobar'
    req = Request.blank('/res1/theid', {
        'CONTENT_LENGTH': str(len(body)),
        'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        'wsgi.input': StringIO.StringIO(body)})
    res = app._handle_request(req)
    print res
    assert res.status == '200 OK'
    assert res._headers['Content-MD5'] == '8d5a8ef21b4afff94c937faabfdf11fa'
    assert res.body == "<response>GET was called with id theid, " \
        "foo None</response>"


def test_app_head_revert_to_get_simple():
    """Application converts a HEAD to a GET request but doesn't send body."""
    app = wsgiservice.get_app(globals())
    body = 'foo=42&baz=foobar'
    req = Request.blank('/res1/theid', {
        'REQUEST_METHOD': 'HEAD',
        'CONTENT_LENGTH': str(len(body)),
        'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        'wsgi.input': StringIO.StringIO(body)})
    res = app._handle_request(req)
    print res
    assert res.status == '200 OK'
    assert res.body == ''


def test_app_post_simple():
    """Application handles normal POST request."""
    app = wsgiservice.get_app(globals())
    body = 'foo=42&baz=foobar'
    req = Request.blank('/res1/theid', {
        'REQUEST_METHOD': 'POST', 'CONTENT_LENGTH': str(len(body)),
        'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        'wsgi.input': StringIO.StringIO(body)})
    res = app._handle_request(req)
    print res
    assert res.status == '200 OK'
    assert res.body == "<response>POST was called with id theid, " \
        "foo 42</response>"


def test_app_wsgi():
    """Application instance works as a WSGI application."""
    app = wsgiservice.get_app(globals())
    env = Request.blank('/res1/theid.json').environ
    start_response = mox.MockAnything()
    start_response('200 OK', [('Content-Length', '40'),
        ('Content-Type', 'application/json; charset=UTF-8'),
        ('Content-MD5', 'd6fe631718727b542d2ecb70dfd41e4b')])
    mox.Replay(start_response)
    res = app(env, start_response)
    print res
    mox.Verify(start_response)
    assert res == ['"GET was called with id theid, foo None"']


def test_validation_method():
    """Resource validates a method parameter which was set on the method."""
    inst = Resource1(None, None, None)
    inst.validate_param(inst.POST, 'foo', '9')


def test_validation_class():
    """Resource validates a method parameter which was set on the class."""
    inst = Resource1(None, None, None)
    inst.validate_param(inst.GET, 'id', 'anyid')


def test_validation_with_re_none_value():
    """Resource rejects empty values if a validation is defined."""
    inst = Resource1(None, None, None)
    try:
        inst.validate_param(inst.GET, 'id', None)
    except wsgiservice.exceptions.ValidationException, e:
        print e
        assert str(e) == 'Value for id must not be empty.'
    else:
        assert False, "Expected an exception!"


def test_validation_with_re_mismatch():
    """Resource rejects invalid values by regular expression."""
    inst = Resource1(None, None, None)
    try:
        inst.validate_param(inst.GET, 'id', 'fo')
    except wsgiservice.exceptions.ValidationException, e:
        print e
        assert str(e) == 'id value fo does not validate.'
    else:
        assert False, "Expected an exception!"


def test_validation_with_re_mismatch_toolong():
    """Resource rejects invalid values by regular expression."""
    inst = Resource1(None, None, None)
    try:
        inst.validate_param(inst.GET, 'id', 'fooobarrr')
    except wsgiservice.exceptions.ValidationException, e:
        print e
        assert str(e) == 'id value fooobarrr does not validate.'
    else:
        assert False, "Expected an exception!"


def test_with_expires():
    """expires decorator correctly sets the Cache-Control header."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res3')
    res = app._handle_request(req)
    print str(res)
    print res._headers
    assert res._headers['Cache-Control'] == 'max-age=86400'


def test_with_expires_vary():
    """expires decorator can set the Vary header."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res6/uid')
    res = app._handle_request(req)
    print str(res)
    print res._headers
    assert res._headers['Cache-Control'] == 'max-age=86400'
    assert res._headers['Vary'] == 'Authorization, Accept'


def test_with_expires_calculations():
    """expires decorator correctly sets the Expires header."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4')
    res = app._handle_request(req)
    print res._headers
    assert res._headers['Cache-Control'] == 'max-age=138'
    assert res._headers['Expires'] == 'Mon, 20 Apr 2009 17:55:45 GMT'


def test_with_expires_calculations_double_wrapped():
    """Wrapped expires decorators work by just using the last one."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4', {'REQUEST_METHOD': 'POST'})
    res = app._handle_request(req)
    print str(res)
    print res._headers
    assert res._headers['Cache-Control'] == 'max-age=138'
    assert res._headers['Expires'] == 'Mon, 20 Apr 2009 17:55:45 GMT'


def test_etag_generate():
    """ETags are calculated by adding the extension to the custom etag."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid')
    res = app._handle_request(req)
    print res._headers
    assert res._headers['ETag'] == '"myid_xml"'


def test_etag_generate_json():
    """ETags are calculated by adding the extension to the custom etag."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid', {'HTTP_ACCEPT': 'application/json'})
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_json"'


def test_etag_generate_json_ext():
    """ETags are calculated by adding the extension to the custom etag."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4.json?id=myid')
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_json"'


def test_etag_if_match_false():
    """A GET request with a non-matching If-Match returns 412."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_MATCH': '"otherid"'})
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_xml"'
    assert res.status == '412 Precondition Failed'


def test_etag_if_match_true():
    """A GET request with a matching If-Match passes."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid', {'HTTP_IF_MATCH': '"myid_xml"'})
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_xml"'
    assert res.status == '200 OK'


def test_etag_if_match_not_set():
    """A GET request without an If-Match header passes."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid')
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_xml"'
    assert res.status == '200 OK'


def test_etag_if_none_match_get_true():
    """A GET request with a matching If-None-Match returns 304."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid', {'HTTP_IF_NONE_MATCH': '"myid_xml"'})
    res = app._handle_request(req)
    print res
    assert res.body == ''
    assert res._headers['ETag'] == '"myid_xml"'
    assert res.status == '304 Not Modified'
    assert 'Content-Type' not in res.headers


def test_etag_if_none_match_head_true():
    """A HEAD request with a matching If-None-Match returns 304."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_NONE_MATCH': '"myid_xml"', 'REQUEST_METHOD': 'HEAD'})
    res = app._handle_request(req)
    print res
    assert res.body == ''
    assert res._headers['ETag'] == '"myid_xml"'
    assert res.status == '304 Not Modified'


def test_etag_if_none_match_post_true():
    """A POST request with a matching If-None-Match returns 412."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_NONE_MATCH': '"myid_xml"', 'REQUEST_METHOD': 'POST'})
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_xml"'
    assert res.status == '412 Precondition Failed'


def test_etag_if_none_match_false():
    """A GET request with a non-matching If-None-Match executes normally."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_NONE_MATCH': '"otherid"'})
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_xml"'
    assert res.status == '200 OK'


def test_modified_generate():
    """Resource generates a good Last-Modified response header."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid')
    res = app._handle_request(req)
    print res._headers
    assert res._headers['Last-Modified'] == 'Fri, 01 May 2009 14:30:00 GMT'


def test_if_modified_since_false():
    """A GET request with a matching If-Modified-Since returns 304."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_MODIFIED_SINCE': 'Fri, 01 May 2009 14:30:00 GMT'})
    res = app._handle_request(req)
    print res
    assert res.body == ''
    assert res._headers['Last-Modified'] == 'Fri, 01 May 2009 14:30:00 GMT'
    assert res._headers['ETag'] == '"myid_xml"'
    assert res.status == '304 Not Modified'


def test_if_modified_since_true():
    """A GET request with an outdated If-Modified-Since passes."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_MODIFIED_SINCE': 'Fri, 01 May 2009 14:18:10 GMT'})
    res = app._handle_request(req)
    print res
    assert res._headers['Last-Modified'] == 'Fri, 01 May 2009 14:30:00 GMT'
    assert res.status == '200 OK'


def test_if_unmodified_since_false():
    """A GET request with an outdated If-Unmodified-Since returns 412."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_UNMODIFIED_SINCE': 'Fri, 01 May 2009 12:30:00 GMT'})
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_xml"'
    assert res._headers['Last-Modified'] == 'Fri, 01 May 2009 14:30:00 GMT'
    assert res.status == '412 Precondition Failed'


def test_if_unmodified_since_false_head():
    """A HEAD request with an outdated If-Unmodified-Since returns 412."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_UNMODIFIED_SINCE': 'Thu, 30 Apr 2009 19:30:00 GMT',
        'REQUEST_METHOD': 'HEAD'})
    res = app._handle_request(req)
    print res
    assert res.body == ''
    assert res._headers['ETag'] == '"myid_xml"'
    assert res._headers['Last-Modified'] == 'Fri, 01 May 2009 14:30:00 GMT'
    assert res.status == '412 Precondition Failed'


def test_if_unmodified_since_false_post():
    """A POST request with an outdated If-Unmodified-Since returns 412."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_UNMODIFIED_SINCE': 'Thu, 30 Apr 2009 19:30:00 GMT',
        'REQUEST_METHOD': 'POST'})
    res = app._handle_request(req)
    print res
    print res.status
    assert res._headers['ETag'] == '"myid_xml"'
    assert res._headers['Last-Modified'] == 'Fri, 01 May 2009 14:30:00 GMT'
    assert res.status == '412 Precondition Failed'


def test_if_unmodified_since_true():
    """A GET request with a current If-Unmodified-Since returns 200."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res4?id=myid',
        {'HTTP_IF_UNMODIFIED_SINCE': 'Fri, 01 May 2009 14:30:00 GMT',
        'REQUEST_METHOD': 'POST'})
    res = app._handle_request(req)
    print res
    assert res._headers['ETag'] == '"myid_xml"'
    assert res._headers['Last-Modified'] == 'Fri, 01 May 2009 14:30:00 GMT'
    assert res.status == '200 OK'


def test_verify_content_md5_invalid():
    """A request with a body that does not match Content-MD5 returns 400."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res1/theid', {
        'HTTP_CONTENT_MD5': '89d5739baabbbe65be35cbe61c88e06d',
        'wsgi.input': StringIO.StringIO('foobar')})
    res = app._handle_request(req)
    print res
    print res.status
    print res._headers
    assert 'ETag' not in res._headers
    assert 'Last-Modified' not in res._headers
    assert res.status == '400 Bad Request'
    assert res.body == '<response><error>Invalid Content-MD5 request ' \
        'header.</error></response>'


def test_verify_content_md5_valid():
    """A request with a body that matches Content-MD5 passes."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res1/theid', {
        'HTTP_CONTENT_MD5': '89d5739baabbbe65be35cbe61c88e06d',
    })
    req.body_file = StringIO.StringIO('Foobar')
    res = app._handle_request(req)
    print res
    assert res.status == '200 OK'


def test_exception_json():
    """An exception is serialized as a dictionary in JSON."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res5?throw=1', {'HTTP_ACCEPT': 'application/json'})
    res = app._handle_request(req)
    print res
    assert res.status == '500 Internal Server Error'
    assert res.body == '{"error": "Some random exception."}'


def test_exception_xml():
    """An exception is serialized as an error response in XML."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res5?throw=1')
    res = app._handle_request(req)
    print res
    assert res.status == '500 Internal Server Error'
    assert res.body == '<response><error>Some random exception.' \
        '</error></response>'


def test_res6_default():
    """Resource6 works normally for keys which exist on the resource."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res6/uid')
    res = app._handle_request(req)
    print res
    assert res.status == '200 OK'
    assert res.body == '<response>works</response>'


def test_notfound_xml():
    """Requests that cause a NOT_FOUND exception return 404."""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/res6/foo')
    res = app._handle_request(req)
    print res
    assert res.status == '404 Not Found'
    assert res.body == '<response><error>Not Found</error></response>'


class AbstractResource(wsgiservice.Resource):
    """This resource should not be added to the application as it doesn't
    have a path. (Verified by test_getapp)
    """


class Resource1(wsgiservice.Resource):
    _path = '/res1/{id}'
    _validations = {'id': {'re': '[a-z]{5}'}}

    def GET(self, id, foo):
        return 'GET was called with id {0}, foo {1}'.format(id, foo)

    def POST(self, id, foo):
        return 'POST was called with id {0}, foo {1}'.format(id, foo)

    POST._validations = {'foo': {'re': '[0-9]+'}}


class Resource2(wsgiservice.Resource):
    _path = '/res2'

    def POST(self):
        wsgiservice.raise_201(self, '/res2/test')

    def PUT(self):
        wsgiservice.raise_201(self, 'foo')


class Resource3(AbstractResource):
    _path = '/res3'

    @wsgiservice.expires(timedelta(days=1))
    def GET(self, id):
        return "Called with id: {0}".format(id)


class Resource4(wsgiservice.Resource):
    _path = '/res4'

    @wsgiservice.expires(138, currtime=lambda: 1240250007)
    def GET(self, id):
        return "Called with id: {0}".format(id)

    @wsgiservice.expires(139, currtime=lambda: 1240250007)
    @wsgiservice.expires(138, currtime=lambda: 1240250007)
    def POST(self, id):
        return "POST Called with id: {0}".format(id)

    def get_etag(self, id):
        if id:
            return id[0] + '"' + id[1:]

    def get_last_modified(self, id):
        from webob import UTC
        from datetime import datetime
        return datetime(2009, 5, 1, 14, 30, tzinfo=UTC)


class Resource5(wsgiservice.Resource):
    _path = '/res5'

    def GET(self, throw):
        if throw == '1':
            raise Exception("Some random exception.")
        else:
            return 'Throwing nothing'


class Resource6(wsgiservice.Resource):

    class DummyException(Exception):
        pass

    NOT_FOUND = (KeyError, DummyException)
    _path = '/res6/{id}'
    items = {'uid': 'works'}

    @wsgiservice.expires(timedelta(days=1), vary=['Authorization'])
    def GET(self, id):
        return self.items[id]

class NotAResource():
    def __getattr__(self, name):
        return name

not_a_class = NotAResource()

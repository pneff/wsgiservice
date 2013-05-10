import json
from webob import Request
import wsgiservice
import wsgiservice.application
import wsgiservice.exceptions

def test_post_json_object():
    """Create object with JSON request body"""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/humans', {'REQUEST_METHOD': 'POST', 'HTTP_ACCEPT': 'application/json'})
    req.content_type = 'application/json'
    req.body = json.dumps({'name': 'flavio'})
    res = app._handle_request(req)
    print res
    assert res.status == '200 OK'
    assert res.body == '{"id": "theid", "name": "flavio"}'

def test_put_json_object():
    """Updating object with JSON request body"""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/humans/theid', {'REQUEST_METHOD': 'PUT', 'HTTP_ACCEPT': 'application/json'})
    req.content_type = 'application/json'
    req.body = json.dumps({'id': 'theid', 'name': 'patrice'})
    res = app._handle_request(req)
    print res
    assert res.status == '200 OK'
    assert res.body == '{"id": "theid", "name": "patrice"}'

def test_post_xml_object_fail():
    """Create object with XML request body not supported"""
    app = wsgiservice.get_app(globals())
    req = Request.blank('/humans', {'REQUEST_METHOD': 'POST', 'HTTP_ACCEPT': 'application/xml'})
    req.content_type = 'application/xml'
    req.body = "<name>patrice</name>"
    res = app._handle_request(req)
    print res
    assert res.status == '400 Bad Request'


class Humans(wsgiservice.Resource):
    _path = '/humans'
    _validations = {'name': {'re': '[a-z]+'}}

    def POST(self, name):
        return {'id': 'theid', 'name': 'flavio'}

class Human(wsgiservice.Resource):
    _path = '/humans/{id}'
    _validations = {'id': {'re': '[a-z]{5}'}, 'name': {'re': '[a-z]+'}}

    def PUT(self, id, name):
        return {'id': 'theid', 'name': 'patrice'}

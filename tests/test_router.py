import wsgiservice.routing

def test_one_resource():
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/foo/my_id')
    print retval
    assert retval[0]['id'] == 'my_id'
    assert retval[0]['_extension'] is None
    assert retval[1] is DummyResource1

def test_one_resource_extension_xml():
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/foo/my_id.xml')
    print retval
    assert retval[0]['id'] == 'my_id'
    assert retval[0]['_extension'] == '.xml'
    assert retval[1] is DummyResource1

def test_one_resource_extension_json():
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/foo/other_id.json')
    print retval
    assert retval[0]['id'] == 'other_id'
    assert retval[0]['_extension'] == '.json'
    assert retval[1] is DummyResource1

def test_one_resource_extension_unknown():
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/foo/other_id.plain')
    print retval
    assert retval[0]['id'] == 'other_id.plain'
    assert retval[0]['_extension'] is None
    assert retval[1] is DummyResource1

def test_one_resource_unknown_path():
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/anything')
    print retval
    assert retval is None


class DummyResource1(object):
    _path = '/foo/{id}'

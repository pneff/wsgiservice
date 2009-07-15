import wsgiservice.routing


def test_one_resource():
    """Route matches for one resource and path parameter is extracted."""
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/foo/my_id')
    print retval
    assert retval[0]['id'] == 'my_id'
    assert retval[0]['_extension'] is None
    assert retval[1] is DummyResource1


def test_one_resource_extension_xml():
    """Extensions are also extracted from the path if available (XML)."""
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/foo/my_id.xml')
    print retval
    assert retval[0]['id'] == 'my_id'
    assert retval[0]['_extension'] == '.xml'
    assert retval[1] is DummyResource1


def test_one_resource_extension_json():
    """Extensions are also extracted from the path if available (JSON)."""
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/foo/other_id.json')
    print retval
    assert retval[0]['id'] == 'other_id'
    assert retval[0]['_extension'] == '.json'
    assert retval[1] is DummyResource1


def test_one_resource_extension_unknown():
    """Unknown extensions are treated as part of the path parameters."""
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/foo/other_id.plain')
    print retval
    assert retval[0]['id'] == 'other_id.plain'
    assert retval[0]['_extension'] is None
    assert retval[1] is DummyResource1


def test_one_resource_unknown_path():
    """None is returned for unknown paths."""
    router = wsgiservice.routing.Router([DummyResource1])
    retval = router('/anything')
    print retval
    assert retval is None


def test_two_resources():
    """Routing for two resources works."""
    router = wsgiservice.routing.Router([DummyResource2, DummyResource1])
    _assert_two_resources(router)


def test_two_resources_priorities():
    """The more specific path takes precedence over the other one."""
    router = wsgiservice.routing.Router([DummyResource1, DummyResource2])
    _assert_two_resources(router)


def test_two_resources_priorities_large():
    """The more specific path takes precedence over the other one."""
    router = wsgiservice.routing.Router([DummyResource1, DummyResource3])
    retval = router('/foo/id')
    print retval
    assert retval[0]['id'] == 'id'
    assert retval[0]['_extension'] is None
    assert retval[1] is DummyResource1, retval[1]
    retval = router('/foo/anything/else')
    print retval
    assert retval[0]['_extension'] is None
    assert retval[1] is DummyResource3, retval[1]


def test_custom_extension():
    """Custom extensions of a resource is recognized for routes."""
    router = wsgiservice.routing.Router([DummyResource3])
    retval = router('/foo/anything/else.txt')
    print retval
    assert retval is not None
    assert retval[0]['_extension'] == '.txt'
    assert retval[1] is DummyResource3


def test_custom_extension_multiple():
    """Custom extensions of a resource is recognized for routes."""
    router = wsgiservice.routing.Router([DummyResource2, DummyResource3])
    retval = router('/foo/anything/else.txt')
    print retval
    assert retval is not None
    assert retval[0]['_extension'] == '.txt'
    assert retval[1] is DummyResource3


def test_custom_extension_per_resource():
    """Custom extensions only apply to the resource where it's defined."""
    router = wsgiservice.routing.Router([DummyResource2, DummyResource3])
    retval = router('/foo/bar.txt')
    print retval
    assert retval is None


class DummyResource1(wsgiservice.Resource):
    _path = '/foo/{id}'


class DummyResource2(wsgiservice.Resource):
    _path = '/foo/id'


class DummyResource3(wsgiservice.Resource):
    _path = '/foo/anything/else'
    EXTENSION_MAP = [
        ('.xml', 'text/xml'),
        ('.json', 'application/json'),
        ('.txt', 'text/plain'),
    ]


def _assert_two_resources(router):
    """Helper for some of the test_two_resources_* tests"""
    retval = router('/foo/id')
    print retval
    assert retval[0]['_extension'] is None
    assert retval[1] is DummyResource2, retval[1]
    retval = router('/foo/anything')
    print retval
    assert retval[0]['id'] == 'anything'
    assert retval[0]['_extension'] is None
    assert retval[1] is DummyResource1, retval[1]

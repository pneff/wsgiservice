# -*- coding: utf-8 -*-
from wsgiservice.xmlserializer import dumps


def test_simple():
    """Simple dictionary."""
    s = dumps({'foo': 'bar', 'baz': 'bar'}, 'response')
    print(s)
    assert s.startswith('<response>')
    assert '<foo>bar</foo>' in s
    assert '<baz>bar</baz>' in s
    assert s.endswith('</response>')


def test_serialisation_bool():
    """XML serialization uses the lower-case string value for booleans."""
    s = dumps(True, 'response')
    print(s)
    assert s == '<response>true</response>'


def test_serialisation_unicode():
    """Unicode strings are converted to UTF-8."""
    s = dumps({'test': 'gfröhrli'}, 'response')
    print(s)
    assert s == '<response><test>gfröhrli</test></response>'

# -*- coding: utf-8 -*-
from wsgiservice.xmlserializer import dumps


def test_simple():
    """Simple dictionary."""
    s = dumps({'foo': 'bar', 'baz': 'bar'}, 'response')
    print s
    assert s.startswith('<response>')
    assert '<foo>bar</foo>' in s
    assert '<baz>bar</baz>' in s
    assert s.endswith('</response>')


def test_serialisation_bool():
    """XML serialization uses the lower-case string value for booleans."""
    s = dumps(True, 'response')
    print s
    assert s == '<response>true</response>'


def test_serialisation_unicode():
    """Unicode strings are converted to UTF-8."""
    s = dumps({'test': u'gfröhrli'}, 'response')
    print s
    assert s == '<response><test>gfröhrli</test></response>'


def test_attrib_config():
    """Create attributes."""
    s = dumps({'link': {'href': 'http://www', 'item': 'Myitem'}}, None,
        {'link': ('href',)})
    print s
    assert s == '<link href="http://www"><item>Myitem</item></link>'


def test_attrib_config_nochildren():
    """Create attributes, make the tag self-closing."""
    s = dumps({'link': {'href': 'http://www', 'item': 'Myitem'}}, None,
        {'link': ('href', 'item')})
    print s
    assert s == '<link item="Myitem" href="http://www"/>'


def test_attrib_escape():
    """All special characters are quoted."""
    s = dumps({'link': {'href': 'a"fü<hl>e&r'}}, None, {'link': ('href')})
    print s
    assert s == '<link href=\'a"fü&lt;hl&gt;e&amp;r\'/>'


def test_attrib_escape_quotes():
    """If both quote characters are used, then escape."""
    s = dumps({'link': {'href': 'a"il\'ia'}}, None, {'link': ('href')})
    print s
    assert s == '<link href="a&quot;il\'ia"/>'


def test_attrib_wildcard():
    """The * selector escapes all attributes of an element."""
    s = dumps({'link': {'href': 'testing'}}, None, {'link': ('*')})
    print s
    assert s == '<link href="testing"/>'

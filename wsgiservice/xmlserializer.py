"""Helper to convert Python data structures into XML. Used so we can return
intuitive data from resource methods which are usable as JSON but can also be
returned as XML.
"""

from xml.sax.saxutils import escape as xml_escape
from xml.sax.saxutils import quoteattr


def dumps(obj, root_tag, attrib_config=None):
    """Serialize a Python object to an XML string.

    :param obj: Python object to serialize, typically a dictionary
    :type obj: Any valid Python value
    :param root_tag: Name of the root tag to wrap around the content. Can
                     be `None` for no root tag.
    :type root_tag: string
    :param attrib_config: Dictionary indicating which dictionary items should
                          be inlined as attributes to their parent element.
                          The key is the tag name for which attributes are to
                          be inlined and the value is a tuple of all keys
                          which are to be inlined.
    :type attrib_config: dict

    :rtype: :class:`str`
    """
    if not attrib_config:
        attrib_config = {}
    xml = _get_xml_value(obj, attrib_config)
    if root_tag is None:
        return xml
    else:
        root = root_tag
        return '<' + root + '>' + xml + '</' + root + '>'


def _get_xml_value(value, attrib_config):
    """Convert an individual value to an XML string. Calls itself
    recursively for dictionaries and lists.

    Uses some heuristics to convert the data to XML:
        - In dictionaries, the keys become the tag name.
        - In lists the tag name is 'child' with an order-attribute giving
          the list index.
        - All other values are included as is.

    All values are escaped to fit into the XML document.

    :param value: The value to convert to XML.
    :type value: Any valid Python value
    :rtype: string
    """
    retval = []
    if isinstance(value, dict):
        retval += _get_xml_value_dict(value, attrib_config)
    elif isinstance(value, list):
        retval += _get_xml_value_list(value, attrib_config)
    elif isinstance(value, bool):
        retval.append(xml_escape(str(value).lower()))
    elif isinstance(value, unicode):
        retval.append(xml_escape(value.encode('utf-8')))
    else:
        retval.append(xml_escape(str(value)))
    return "".join(retval)


def _get_xml_value_dict(value, attrib_config):
    """Serialize a dictionary to XML."""
    retval = []
    for key, value in value.iteritems():
        retval += _get_xml_tag(key, value, attrib_config)
    return retval


def _get_xml_value_list(value, attrib_config):
    """Serialize a list to XML."""
    retval = []
    for key, value in enumerate(value):
        retval += _get_xml_tag('child', value, attrib_config,
            {'order': key})
    return retval


def _get_xml_tag(tag_name, content, attrib_config, attributes={}):
    """Return an XML tag. Implements the logic for attribute handling."""
    retval = []
    attributes = dict(attributes) # Copy
    tag_name = str(tag_name)
    this_attrib_config = attrib_config.get(tag_name, [])
    if isinstance(content, dict):
        # Get attributes from the list
        content = dict(content) # Copy
        for key in content.keys():
            if key in this_attrib_config:
                attributes[key] = content[key]
                del content[key]
    retval.append('<' + xml_escape(tag_name))
    for attrib, value in attributes.iteritems():
        retval.append(' ' + xml_escape(str(attrib)) + '=' +
            quoteattr(str(value)))
    if content:
        retval.append('>')
        retval.append(_get_xml_value(content, attrib_config))
        retval.append('</' + xml_escape(tag_name) + '>')
    else:
        retval.append('/>')
    return retval

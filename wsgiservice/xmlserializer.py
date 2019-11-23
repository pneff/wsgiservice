"""Helper to convert Python data structures into XML. Used so we can return
intuitive data from resource methods which are usable as JSON but can also be
returned as XML.
"""
import re
from xml.sax.saxutils import escape as xml_escape

from six import unichr as chr
from six import binary_type, text_type

# Regular expression matching all the illegal XML characters.
RE_ILLEGAL_XML = re.compile(
    u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])|([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' %
    (chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
     chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
     chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff)))


def dumps(obj, root_tag):
    """Serialize :arg:`obj` to an XML :class:`str`.
    """
    xml = _get_xml_value(obj)
    if xml:
        # Remove invalid XML
        xml = RE_ILLEGAL_XML.sub('', xml)
    if root_tag is None:
        return xml
    else:
        root = root_tag
        return '<' + root + '>' + xml + '</' + root + '>'


def _get_xml_value(value):
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
        for key, value in value.items():
            retval.append('<' + xml_escape(text_type(key)) + '>')
            retval.append(_get_xml_value(value))
            retval.append('</' + xml_escape(text_type(key)) + '>')
    elif isinstance(value, list):
        for key, value in enumerate(value):
            retval.append('<child order="' + xml_escape(text_type(key)) + '">')
            retval.append(_get_xml_value(value))
            retval.append('</child>')
    elif isinstance(value, bool):
        retval.append(xml_escape(text_type(value).lower()))
    elif isinstance(value, binary_type):
        retval.append(xml_escape(value.encode('utf-8')))
    elif isinstance(value, text_type):
        retval.append(xml_escape(value))
    else:
        retval.append(xml_escape(text_type(value)))
    return "".join(retval)

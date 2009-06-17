import json
import logging
import webob
from xml.sax.saxutils import escape as xml_escape

logger = logging.getLogger(__name__)

class Resource(object):
    """Base class for all WsgiService resources. A resourse is a unique REST
    endpoint which accepts different methods for different actions.
    
    For each HTTP call the corresponding method (equal to the HTTP method)
    will be called.
    """
    XML_ROOT_TAG = 'response'

    def __init__(self, request, response, path_params):
        self.request = request
        self.response = response
        self.path_params = path_params

    def get_etag(self):
        """Returns a string to be used as the ETag for this resource. Used to
        set the ``ETag`` response headers and for conditional requests using
        the ``If-Match`` and ``If-None-Match`` request headers.
        """
        return None

    def get_last_modified(self):
        """Return a :class:`datetime.datetime` object of the when the resource
        was last modified. Used to set the ``Last-Modified`` response header
        and for conditional requests using the ``If-Modified-Since`` and
        ``If-Unmodified-Since`` request headers.

        :rtype: :class:`datetime.datetime`
        """
        return None

    def get_allowed_methods(self):
        """Return a coma-separated list of method names that are allowed on
        this instance. Returns all upper-case method names. Useful to set the
        ``Allowed`` response header.
        """
        return ", ".join([method for method in dir(self)
            if method.upper() == method
            and callable(getattr(self, method))])

    def to_application_json(self, raw):
        """Augments the given response object by setting the JSON response
        headers and converting the `raw` Python object into a JSON string.
        
        :param raw: The return value of the resource method.
        :type raw: Any valid Python object
        """
        logger.debug("Converting body to application/json")
        self.response.body = json.dumps(raw)

    def to_text_xml(self, raw):
        """Augments the given response object by setting the XML response
        headers and converting the `raw` Python object into an XML string.
        
        Uses some heuristics to convert the data to XML:
          - Default root tag is 'response', but that can be overwritting by
            overwriting the variable XML_ROOT_TAG instance variable.
          - In lists and dictionaries, the keys become the tag name.
          - All other values are appended as is.
        
        :param raw: The return value of the resource method.
        :type raw: Any valid Python object
        """
        logger.debug("Converting body to text/xml")
        xml = self._get_xml_value(raw)
        if self.XML_ROOT_TAG is None:
            self.response.body = xml
        else:
            self.response.body = '<' + self.XML_ROOT_TAG + '>' + xml + \
                '</' + self.XML_ROOT_TAG + '>'

    def _get_xml_value(self, value):
        """Convert an individual value to an XML string."""
        retval = []
        if isinstance(value, dict):
            for key, value in value.iteritems():
                retval.append('<' + xml_escape(str(key)) + '>')
                retval.append(self._get_xml_value(value))
                retval.append('</' + xml_escape(str(key)) + '>')
        elif isinstance(value, list):
            for key, value in enumerate(value):
                retval.append('<' + xml_escape(str(key)) + '>')
                retval.append(self._get_xml_value(value))
                retval.append('</' + xml_escape(str(key)) + '>')
        else:
            retval.append(xml_escape(str(value)))
        return "".join(retval)

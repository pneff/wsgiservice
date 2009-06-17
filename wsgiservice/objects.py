"""Objects to abstract the response handling."""
import cgi
import hashlib
import json
import logging
import re
from xml.sax.saxutils import escape as xml_escape
import webob

logger = logging.getLogger(__name__)

class Response(object):
    """Represents the response to be sent to the client. Handles content
    negotiation and some header generation where possible.
    
    :param body: Body to output to the browser. Will be transformed to the
                 ideal format based on content negotiation. Set to ``None``
                 to avoid sending out a response body.
    :type body: any valid Python object
    :param environ: The WSGI environment dictionary.
    :type environ: dict
    :param resource: The resource which was used to generate this response if
                     any.
    :type resource: :class:`wsgiservice.Resource`
    :param method: The method which was used to generate this respons if any.
    :type method: method of :class:`wsgiservice.Resource`
    :param headers: Any headers that are to be sent to the client.
    :type headers: dict
    :param status: Status code to send. The correct description will be added
                   based on this code.
    :type status: int
    :param extension: The extension which was passed in from the routing
                      engine. This is used for content negotiation to override
                      any ``Accept`` request headers.
    :type extension: str
    """
    _status_map = {
        100: '100 Continue',
        101: '101 Switching Protocols',
        200: '200 OK',
        201: '201 Created',
        202: '202 Accepted',
        203: '203 Non-Authoritative Information',
        204: '204 No Content',
        205: '205 Reset Content',
        206: '206 Partial Content',
        300: '300 Multiple Choices',
        301: '301 Moved Permanently',
        302: '302 Found',
        303: '303 See Other',
        304: '304 Not Modified',
        305: '305 Use Proxy',
        306: '306 (Unused)',
        307: '307 Temporary Redirect',
        400: '400 Bad Request',
        401: '401 Unauthorized',
        402: '402 Payment Required',
        403: '403 Forbidden',
        404: '404 Not Found',
        405: '405 Method Not Allowed',
        406: '406 Not Acceptable',
        407: '407 Proxy Authentication Required',
        408: '408 Request Timeout',
        409: '409 Conflict',
        410: '410 Gone',
        411: '411 Length Required',
        412: '412 Precondition Failed',
        413: '413 Request Entity Too Large',
        414: '414 Request-URI Too Long',
        415: '415 Unsupported Media Type',
        416: '416 Requested Range Not Satisfiable',
        417: '417 Expectation Failed',
        500: '500 Internal Server Error',
        501: '501 Not Implemented',
        502: '502 Bad Gateway',
        503: '503 Service Unavailable',
        504: '504 Gateway Timeout',
        505: '505 HTTP Version Not Supported',
    }
    _extension_map = {
        '.xml': 'text/xml',
        '.json': 'application/json',
    }

    def __init__(self, body, environ, resource=None, method=None,
            headers=None, status=200, extension=None):
        self._environ = environ
        self._resource = resource
        if environ.get('REQUEST_METHOD', '') == 'HEAD':
            body = None
        self._body = body
        self._method = method
        self._available_types = ['text/xml', 'application/json']
        if extension in self._extension_map:
            self.type = self._extension_map[extension]
            logger.debug("Using response type %s based on extension %s",
                self.type, extension)
        else:
            request = webob.Request(environ)
            self.type = request.accept.first_match(self._available_types)
            logger.debug("Using response type %s", self.type)
        self.convert_type = self.type
        if body is not None and method and self.convert_type:
            to_type = re.sub('[^a-zA-Z_]', '_', self.convert_type)
            to_type_method = 'to_' + to_type
            if hasattr(method, to_type_method):
                self._body = getattr(method, to_type_method)(self._body)
                self.convert_type = None
        self._headers = {'Content-Type': self.type + '; charset=UTF-8'}
        if headers:
            for key in headers:
                self._headers[key] = headers[key]
        if not extension in self._extension_map:
            if 'Vary' in self._headers:
                self._headers['Vary'] = self._headers['Vary'] + ', Accept'
            else:
                self._headers['Vary'] = 'Accept'
        self.status = self._status_map[status]

    @property
    def headers(self):
        """Dictionary of all headers currently to be sent to the browser."""
        return self._headers.items()

    def __str__(self):
        if self._body is None:
            body = ''
        elif self.convert_type is None:
            # Assume body is already in the correct output format
            body = self._body
        elif self.convert_type == 'application/json':
            logger.debug("Converting body to application/json")
            body = json.dumps(self._body)
        elif self.convert_type == 'text/xml':
            logger.debug("Converting body to text/xml")
            xml = self._to_xml(self._body)
            root_tag = 'response'
            if hasattr(self._method, 'text_xml_root'):
                root_tag = self._method.text_xml_root
            elif hasattr(self._resource, 'text_xml_root'):
                root_tag = self._resource.text_xml_root
            if root_tag is None:
                body = xml
            else:
                body = '<' + root_tag + '>' + xml + '</' + root_tag + '>'
        self._headers['Content-MD5'] = hashlib.md5(body).hexdigest()
        return body

    def _to_xml(self, value):
        """Converts value to XML."""
        retval = []
        if isinstance(value, dict):
            for key, value in value.iteritems():
                retval.append('<' + xml_escape(str(key)) + '>')
                retval.append(self._to_xml(value))
                retval.append('</' + xml_escape(str(key)) + '>')
        elif isinstance(value, list):
            for key, value in enumerate(value):
                retval.append('<' + xml_escape(str(key)) + '>')
                retval.append(self._to_xml(value))
                retval.append('</' + xml_escape(str(key)) + '>')
        else:
            retval.append(xml_escape(str(value)))
        return "".join(retval)


class MiniResponse(object):
    """A small wrapper to return body content and headers easily. Mostly
    needed so that the decorators don't get too complex.
    """
    def __init__(self, body, headers=None):
        self.body = body
        self.headers = headers or {}

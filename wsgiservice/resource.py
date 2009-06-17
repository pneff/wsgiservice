import hashlib
import inspect
import json
import logging
import webob
import re
from xml.sax.saxutils import escape as xml_escape
from wsgiservice.status import *
from wsgiservice.exceptions import ValidationException

logger = logging.getLogger(__name__)

class Resource(object):
    """Base class for all WsgiService resources. A resourse is a unique REST
    endpoint which accepts different methods for different actions.
    
    For each HTTP call the corresponding method (equal to the HTTP method)
    will be called.

    :var XML_ROOT_TAG: The root tag for generated XML output. Used by
        :func:`to_text_xml`. (Default: 'response')
    :var KNOWN_METHODS: List of the known HTTP methods. Used by
        :func:`get_method` to handle methods that are not implemented.
        (Default: All methods defined by the HTTP 1.1 standard :rfc:`2616`)
    :var EXTENSION_MAP: Dictionary mapping file extensions to MIME types. Used
        by :func:`get_content_type` to determine the requested MIME type.
        (Default: '.xml' => 'text/xml' and '.json' => 'application/json')
    """
    XML_ROOT_TAG = 'response'
    KNOWN_METHODS = ['OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                     'TRACE', 'CONNECT']
    EXTENSION_MAP = {
        '.xml': 'text/xml',
        '.json': 'application/json'
    }

    def __init__(self, request, response, path_params):
        self.request = request
        self.response = response
        self.path_params = path_params
    
    def OPTIONS(self):
        """Default implementation of the OPTIONS verb. Outputs a list of
        allowed methods on this resource in the `Allow` response header.
        """
        self.response.headers['Allow'] = self.get_allowed_methods()
    
    def call(self):
        """Main entry point for calling this resource. Handles the method
        dispatching, response conversion, etc. for this resource.
        """
        self.type = self.get_content_type()
        try:
            self.method = self.get_method()
            self.assert_conditions()
            self.response.body_raw = self.call_method(self.method)
        except ResponseException, e:
            # a response was raised, catch it
            self.response = e.response
        except Exception, e:
            self.handle_exception(e)
        self.convert_response()
        return self.response
    
    def get_method(self, method=None):
        """Returns the method to call on this instance as a string. Raises a
        HTTP exception if no method can be found. Aborts with a 405 status
        code for known methods (based on the :attr:`KNOWN_METHODS` list) and a
        501 status code for all other methods.
        """
        if method is None:
            method = self.request.method
        if hasattr(self, method) and callable(getattr(self, method)):
            return method
        elif method == 'HEAD':
            return self.get_method('GET')
        # Error: did not find any method, raise a 405 or 501 exception
        elif method in self.KNOWN_METHODS:
            # Known HTTP methods => 405 Method Not Allowed
            raise_405(self)
        else:
            # Unknown HTTP methods => 501 Not Implemented
            raise_501(self)
    
    def get_content_type(self):
        """Returns the Content Type to serve from either the extension or the
        Accept headers. Uses the :attr:`EXTENSION_MAP` dictionary for all the
        configured MIME types.
        """
        extension = self.path_params.get('_extension')
        if extension in self.EXTENSION_MAP:
            return self.EXTENSION_MAP[extension]
        else:
            # Use the Accept headers
            if self.response.vary is None:
                self.response.vary = ['Accept']
            else:
                self.response.vary.append('Accept')
            return self.request.accept.first_match(self.EXTENSION_MAP.values())
    
    def assert_conditions(self):
        """Handles various HTTP conditions and raises HTTP exceptions to
        abort the request.

            - Content-MD5 request header must match the MD5 hash of the full
              input.
            - If-Match and If-None-Match etags are checked against the ETag of
              this resource.
            - If-Modified-Since and If-Unmodified-Since are checked against
              the modification date of this resource.
        """
        self.assert_condition_md5()
        etag = self.clean_etag(self.call_method('get_etag'))
        self.response.last_modified = self.call_method('get_last_modified')
        self.assert_condition_etag()
        self.assert_condition_last_modified()
    
    def assert_condition_md5(self):
        """If the `Content-MD5` request header is present in the request it's
        verified against the MD5 hash of the request body. If they don't
        match, a 400 HTTP response is returned.
        """
        if 'Content-MD5' in self.request.headers:
            body_md5 = hashlib.md5(self.request.body_file.read()).hexdigest()
            if body_md5 != self.request.headers['Content-MD5']:
                raise_400(self, msg='Invalid Content-MD5 request header.')
    
    def assert_condition_etag(self):
        """If the resource has an ETag (see :func:`get_etag`) the request
        headers `If-Match` and `If-None-Match` are verified. May abort the
        request with 304 or 412 response codes.
        """
        if self.response.etag:
            etag = self.response.etag.replace('"', '')
            if not etag in self.request.if_match:
                raise_412(self, 'If-Match request header does not the resource ETag.')
            if etag in self.request.if_none_match:
                if self.request.method in ('GET', 'HEAD'):
                    raise_304(self)
                else:
                    raise_412(self, 'If-None-Match request header matches resource ETag.')
    
    def assert_condition_last_modified(self):
        """If the resource has a last modified date (see
        :func:`get_last_modified`) the request headers `If-Modified-Since` and
        `If-Unmodified-Since` are verified. May abort the request with 304 or
        412 response codes.
        """
        rq = self.request
        rs = self.response
        if rs.last_modified:
            if rq.if_modified_since and rs.last_modified <= rq.if_modified_since:
                raise_304(self)
            if rq.if_unmodified_since and rs.last_modified > rq.if_unmodified_since:
                raise_412(self, 'Resource is newer than the If-Unmodified-Since request header.')
    
    def get_etag(self):
        """Returns a string to be used as the ETag for this resource. Used to
        set the ``ETag`` response headers and for conditional requests using
        the ``If-Match`` and ``If-None-Match`` request headers.
        """
        return None
    
    def clean_etag(self, etag):
        """Cleans the ETag as returned by get_etag. Will wrap it in quotes
        and append the extension for the current MIME type.
        """
        if etag:
            etag = etag.replace('"', '')
            ext = None
            for key, value in self.EXTENSION_MAP.iteritems():
                if value == self.type:
                    ext = key[1:]
                    break
            if ext:
                etag += '_' + ext
            self.response.etag = '"' +  etag + '"'
    
    def get_last_modified(self):
        """Return a :class:`datetime.datetime` object of the when the resource
        was last modified. Used to set the ``Last-Modified`` response header
        and for conditional requests using the ``If-Modified-Since`` and
        ``If-Unmodified-Since`` request headers.

        :rtype: :class:`datetime.datetime`
        """
        return None
    
    def get_allowed_methods(self):
        """Returns a coma-separated list of method names that are allowed on
        this instance. Useful to set the ``Allowed`` response header.
        """
        return ", ".join([method for method in dir(self)
            if method.upper() == method
            and callable(getattr(self, method))])
    
    def call_method(self, method_name):
        """Call an instance method filling in all the method parameters based
        on their names. The parameters are filled in from the following
        locations (in that order of precedence):

            1. Path parameters from routing
            2. GET parameters
            3. POST parameters

        The return value of the method is then returned.
        """
        method = getattr(self, method_name)
        method_params, varargs, varkw, defaults = inspect.getargspec(method)
        if method_params:
            method_params.pop(0) # pop the self off
        params = []
        for param in method_params:
            value = None
            if param in self.path_params:
                value = self.path_params[param]
            elif param in self.request.GET:
                value = self.request.GET[param]
            elif param in self.request.POST:
                value = self.request.POST[param]
            self.validate_param(method, param, value)
            params.append(value)
        return method(*params)
    
    def validate_param(self, method, param, value):
        """Validates the parameter according to the configurations in the
        _validations dictionary of either the method or the instance. This
        dictionaries are written by the decorator
        :func:`wsgiservice.decorators.validate`.
        """
        rules = None
        if hasattr(method, '_validations') and param in method._validations:
            rules = method._validations[param]
        elif hasattr(method.im_class, '_validations') and param in method.im_class._validations:
            rules = method.im_class._validations[param]
        else:
            return
        if value is None or len(value) == 0:
            raise ValidationException("Value for {0} must not be empty.".format(param))
        elif 're' in rules and rules['re']:
            if not re.search('^' + rules['re'] + '$', value):
                raise ValidationException("{0} value {1} does not validate.".format(param, value))
    
    def convert_response(self):
        """Finish filling the instance's response object so it's ready to be
        served to the client. This includes converting the body_raw property
        to the content type requested by the user if necessary.
        """
        if hasattr(self.response, 'body_raw'):
            if self.response.body_raw is not None:
                to_type = re.sub('[^a-zA-Z_]', '_', self.type)
                to_type_method = 'to_' + to_type
                if hasattr(self, to_type_method):
                    self.response.body = getattr(self, to_type_method)(
                        self.response.body_raw)
            del self.response.body_raw
        self.response.headers['Content-Type'] = self.type + '; charset=UTF-8'
        self.response.content_md5 = hashlib.md5(self.response.body).hexdigest()
    
    def to_application_json(self, raw):
        """Returns the JSON version of the given raw Python object.
        
        :param raw: The return value of the resource method.
        :type raw: Any valid Python object
        :rtype: string
        """
        return json.dumps(raw)
    
    def to_text_xml(self, raw):
        """Returns the XML string version of the given raw Python object.
        
        Uses some heuristics to convert the data to XML:
          - Default root tag is 'response', but that can be overwritting by
            overwriting the variable :attr:`XML_ROOT_TAG` instance variable.
          - In lists and dictionaries, the keys become the tag name.
          - All other values are appended as is.
        
        :param raw: The return value of the resource method.
        :type raw: Any valid Python object
        :rtype: string
        """
        xml = self._get_xml_value(raw)
        if self.XML_ROOT_TAG is None:
            return xml
        else:
            root = self.XML_ROOT_TAG
            return '<' + root + '>' + xml + '</' + root + '>'
    
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
        elif isinstance(value, bool):
            retval.append(xml_escape(str(value).lower()))
        else:
            retval.append(xml_escape(str(value)))
        return "".join(retval)
    

    def handle_exception(self, e):
        """Handles the given exception. By default it will log it, set the
        response code to 500 and output the exception message as an error
        message.
        """
        logger.exception("An exception occured while handling the request.")
        self.response.body_raw = {'error': str(e)}
        self.response.status = 500

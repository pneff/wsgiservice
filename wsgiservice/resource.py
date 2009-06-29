import hashlib
import inspect
import json
import logging
import webob
import re
from xml.sax.saxutils import escape as xml_escape
from wsgiservice.status import *
from wsgiservice.decorators import mount
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
    :var NOT_FOUND: A tuple of exceptions that should be treated as 404. An
        ideal candidate is KeyError if you do dictionary accesses. Used by
        :func:`call` which calls :func:`handle_exception_404` whenever an
        exception from this tuple occurs. (Default: Empty tuple)
    :var IGNORED_PATHS: A tuple of absolute paths that should return a 404.
        By default this is used to ignored requests for favicon.ico and
        robots.txt so that browsers don't cause too many exceptions.
    """
    XML_ROOT_TAG = 'response'
    KNOWN_METHODS = ['OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE',
                     'TRACE', 'CONNECT']
    EXTENSION_MAP = {
        '.xml': 'text/xml',
        '.json': 'application/json'
    }
    NOT_FOUND = ()
    IGNORED_PATHS = ('/favicon.ico', '/robots.txt')

    def __init__(self, request, response, path_params, application=None):
        """Constructor. Order of the parameters is not guarantteed, always
        used named parameters.
        """
        self.request = request
        self.response = response
        self.path_params = path_params
        self.application = application
    
    def OPTIONS(self):
        """Default implementation of the OPTIONS verb. Outputs a list of
        allowed methods on this resource in the `Allow` response header.
        """
        self.response.headers['Allow'] = self.get_allowed_methods()
    
    def __call__(self):
        """Main entry point for calling this resource. Handles the method
        dispatching, response conversion, etc. for this resource.
        Catches all exceptions.

            * :class:`ResponseException`: Replaces the instance's response
              attribute with the one fromthe exception.
            * For all exceptions in the :attr:`NOT_FOUND` tuple
              :func:`handle_exception_404` is called.
            * For all other exceptions deriving from the :class:`Exception`
              base class, the :func:`handle_exception` method is called.
        """
        self.type = self.get_content_type()
        try:
            self.method = self.get_method()
            self.handle_ignored_resources()
            self.assert_conditions()
            self.response.body_raw = self.call_method(self.method)
        except ResponseException, e:
            # a response was raised, catch it
            self.response = e.response
        except self.NOT_FOUND, e:
            self.handle_exception_404(e)
        except ValidationException, e:
            self.handle_exception(e, status=400)
        except Exception, e:
            self.handle_exception(e)
        self.convert_response()
        return self.response
    
    def get_resource(self, resource, **kwargs):
        """Returns a new instance of the resource class passed in as resource.
        This is a helper to make future-compatibility easier when new
        arguments get added to the constructor."""
        return resource(request=self.request, response=self.response,
            path_params=self.path_params, application=self.application,
            **kwargs)
    
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
    
    def handle_ignored_resources(self):
        """Ignore robots.txt and favicon.ico GET requests."""
        if self.method in ('GET', 'HEAD') and self.request.path_qs in (self.IGNORED_PATHS):
            raise_404(self)
    
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
        optional_args = []
        if defaults:
            optional_args = method_params[len(defaults):]
        params = []
        for param in method_params:
            value = None
            if param in self.path_params:
                value = self.path_params[param]
            elif param in self.request.GET:
                value = self.request.GET[param]
            elif param in self.request.POST:
                value = self.request.POST[param]
            elif param in optional_args:
                value = defaults[optional_args.index(param)]
            self.validate_param(method, param, value)
            params.append(value)
        return method(*params)
    
    def validate_param(self, method, param, value):
        """Validates the parameter according to the configurations in the
        _validations dictionary of either the method or the instance. This
        dictionaries are written by the decorator
        :func:`wsgiservice.decorators.validate`.
        
        .. todo:: If the parameter has a default value then don't require a
                  value to be specified.
        .. todo:: Allow validation by type (e.g. header, post, query, etc.)
        """
        rules = self._get_validation(method, param)
        if not rules:
            return
        if value is None or len(str(value)) == 0:
            raise ValidationException("Value for {0} must not be empty.".format(param))
        elif 're' in rules and rules['re']:
            if not re.search('^' + rules['re'] + '$', value):
                raise ValidationException("{0} value {1} does not validate.".format(param, value))
    
    def _get_validation(self, method, param):
        """Return the correct validations dictionary for this parameter or
        None.
        """
        if hasattr(method, '_validations') and param in method._validations:
            return method._validations[param]
        elif hasattr(method.im_class, '_validations') and param in method.im_class._validations:
            return method.im_class._validations[param]
        else:
            return None
    
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
    
    def handle_exception(self, e, status=500):
        """Handles the given exception: logs the exception, sets the response
        code to 500 and outputs the exception message as an error message.
        """
        logger.exception("An exception occured while handling the request: %s", e)
        self.response.body_raw = {'error': str(e)}
        self.response.status = status
    
    def handle_exception_404(self, e):
        """Handles the given exception: logs the exception, sets the response
        code to 404 and outputs a Not Found error message.
        """
        logger.exception("A 404 Not Found exception occured while handling the request.")
        self.response.body_raw = {'error': 'Not Found'}
        self.response.status = 404



@mount('/_internal/help')
class Help(Resource):
    """Provides documentation for all resources of the current application.
    
    .. todo:: Allow documentation of output.
    .. todo:: Use first sentence of docstring for summary, add bigger version
              at the bottom.
    """
    EXTENSION_MAP = {
        '.xml': 'text/xml',
        '.json': 'application/json',
        '.html': 'text/html',
    }
    XML_ROOT_TAG = 'help'

    def GET(self):
        "Returns documentation for the application."
        retval = []
        for res in self.application._resources:
            retval.append({
                'name': res.__name__,
                'desc': self._get_doc(res),
                'properties': {
                    'XML_ROOT_TAG': res.XML_ROOT_TAG,
                    'KNOWN_METHODS': res.KNOWN_METHODS,
                    'EXTENSION_MAP': dict((key[1:], value) for key, value
                        in res.EXTENSION_MAP.iteritems()),
                    'NOT_FOUND': [ex.__name__ for ex in res.NOT_FOUND],
                },
                'methods': self._get_methods(res),
                'path': self.request.script_name + res._path,
            })
        return retval

    def _get_methods(self, res):
        """Return a dictionary of method descriptions for the given resource.
        """
        retval = {}
        instance = res(request=webob.Request.blank('/'),
            response=webob.Response(), path_params={})
        methods = [m.strip() for m in instance.get_allowed_methods().split(',')]
        for method_name in methods:
            method = getattr(res, method_name)
            retval[method_name] = {
                'desc': self._get_doc(method),
                'parameters': self._get_parameters(res, method)
            }
        return retval
    
    def _get_doc(self, obj):
        doc = obj.__doc__
        if doc:
            return doc.strip()
        else:
            return ''
    
    def _get_parameters(self, res, method):
        """Return a parameters dictionary for the given resource/method."""
        method_params, varargs, varkw, defaults = inspect.getargspec(method)
        if method_params:
            method_params.pop(0) # pop the self off
        self._add_path_parameters(method_params, res, method)
        retval = {}
        for param in method_params:
            is_path_param = '{' + param + '}' in res._path
            retval[param] = {
                'path_param': is_path_param,
                'mandatory': is_path_param,
                'validate_re': None,
                'desc': '',
            }
            validation = self._get_validation(method, param)
            if validation:
                retval[param]['validate_re'] = validation['re']
                retval[param]['desc'] = validation['doc'] or ''
        return retval

    def _add_path_parameters(self, method_params, res, method):
        """Extract all path parameters as they are always required even
        though some methods may not have them in their definition.
        """
        for param in re.findall('{([^}]+)}', res._path):
            if param not in method_params:
                method_params.append(param)

    def _get_xml_value(self, value):
        """Treat arrays better."""
        if isinstance(value, list):
            retval = []
            for key, value in enumerate(value):
                retval.append('<resource>')
                retval.append(self._get_xml_value(value))
                retval.append('</resource>')
            return "".join(retval)
        else:
            return Resource._get_xml_value(self, value)

    def to_text_html(self, raw):
        """Returns the HTML string version of the given raw Python object.
        Hard-coded to return a nicely-presented service information document.
        
        :param raw: The return value of the resource method.
        :type raw: Any valid Python object
        :rtype: string

        .. todo:: Treat pragraphs and/or newlines better in output.
        """
        retval = ["""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
                        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
            <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
                <title>Help Example</title>
                <style>
                    /* YUI reset.css */
                    html{color:#000;background:#FFF;}body,div,dl,dt,dd,ul,ol,li,h1,h2,h3,h4,h5,h6,pre,code,form,fieldset,legend,input,button,textarea,p,blockquote,th,td{margin:0;padding:0;}table{border-collapse:collapse;border-spacing:0;}fieldset,img{border:0;}address,caption,cite,code,dfn,em,strong,th,var,optgroup{font-style:inherit;font-weight:inherit;}del,ins{text-decoration:none;}li{list-style:none;}caption,th{text-align:left;}h1,h2,h3,h4,h5,h6{font-size:100%;font-weight:normal;}q:before,q:after{content:'';}abbr,acronym{border:0;font-variant:normal;}sup{vertical-align:baseline;}sub{vertical-align:baseline;}legend{color:#000;}input,button,textarea,select,optgroup,option{font-family:inherit;font-size:inherit;font-style:inherit;font-weight:inherit;}input,button,textarea,select{*font-size:100%;}
                    /* YUI fonts.css */
                    body{font:13px/1.231 arial,helvetica,clean,sans-serif;*font-size:small;*font:x-small;}select,input,button,textarea,button{font:99% arial,helvetica,clean,sans-serif;}table{font-size:inherit;font:100%;}pre,code,kbd,samp,tt{font-family:monospace;*font-size:108%;line-height:100%;}
                    /* YUI base.css */
                    body{margin:10px;}h1{font-size:138.5%;}h2{font-size:123.1%;}h3{font-size:108%;}h1,h2,h3{margin:1em 0;}h1,h2,h3,h4,h5,h6,strong,dt{font-weight:bold;}optgroup{font-weight:normal;}abbr,acronym{border-bottom:1px dotted #000;cursor:help;}em{font-style:italic;}del{text-decoration:line-through;}blockquote,ul,ol,dl{margin:1em;}ol,ul,dl{margin-left:2em;}ol li{list-style:decimal outside;}ul li{list-style:disc outside;}dl dd{margin-left:1em;}th,td{border:1px solid #000;padding:.5em;}th{font-weight:bold;text-align:center;}caption{margin-bottom:.5em;text-align:center;}sup{vertical-align:super;}sub{vertical-align:sub;}p,fieldset,table,pre{margin-bottom:1em;}button,input[type="checkbox"],input[type="radio"],input[type="reset"],input[type="submit"]{padding:1px;}

                    h2 {margin-top: 0;}
                    .resource_details {padding-top: 2em;border-top: 1px dotted #ccc;margin-top: 2em;}
                    .method_details {margin-left: 2em;}
                    
                    /* JS form */
                    form {
                        padding: 1em;
                        border: 1px solid #ccc;
                    }
                    input.error {
                        background: #FCECEC;
                        color: red;
                        border: 1px solid red;
                    }
                    label {
                        font-weight: bold;
                        float: left;
                        width: 10em;
                    }
                    p.form_element, input.submit {
                        clear: left;
                    }
                    div.result {
                        margin-top: 1em;
                    }
                    h4 {
                        margin-bottom: 0.5em;
                    }
                    a.add_input {
                        margin: 0.5em;
                    }
                    .hidden { display: none !important; }
                    a.toggle_details {
                        margin-bottom: 1em;
                        display: block;
                    }
                </style>
                <script>
                /**
                 * Adds a resource's method - a form to the current location with the ability
                 * to submit a request to the service filling in all the parameters.
                 */
                function add_resource_method(target, resource, method_name, method) {
                    new ResourceMethodForm(target, resource, method_name, method);
                }

                function ResourceMethodForm(target, resource, method_name, method) {
                    this.targetName = target;
                    this.target = document.getElementById(target);
                    this.resource = resource;
                    this.method_name = method_name;
                    this.method = method;
                    this.init();
                }

                var pr = ResourceMethodForm.prototype;

                pr.init = function() {
                    var fragment = document.createDocumentFragment();
                    var form = this.create_form(fragment);
                    var input_container = document.createElement('div');
                    this.input_container = input_container;
                    form.appendChild(input_container);
                    this.create_form_params(input_container);
                    this.create_form_buttons(form);
                    this.create_result_field(form);
                    this.target.appendChild(fragment);
                };
                pr.create_form = function(parent) {
                    var form = document.createElement('form');
                    form.action = '';
                    form.target = '_blank';
                    var that = this;
                    form.onsubmit = function() {
                        return that.on_submit();
                    };
                    var h4 = document.createElement('h4');
                    h4.innerHTML = 'Debug form';
                    form.appendChild(h4);

                    parent.appendChild(form);
                    return form;
                };
                pr.create_form_params = function(parent) {
                    for (param in this.method.parameters) {
                        this.create_form_field(parent, 'param', 'text', param);
                    }

                    // Accept header
                    var mimes = [];
                    var emap = this.resource.properties.EXTENSION_MAP;
                    for (extension in emap) {
                        mimes.push(emap[extension]);
                    }
                    this.create_form_field(parent, 'header', 'select', 'Accept', mimes);
                };
                pr.create_form_field = function(parent, type, field_type, name, options) {
                    var id = type + '_' + this.resource['name'] + '_' + this.method_name + '_' + name;
                    var d = document.createElement('div');
                    d.className = type;
                    d.id = id;

                    var input_id = id + '_input';
                    var lbl = document.createElement('label');
                    lbl.innerHTML = name;
                    if (type == 'header') {
                        lbl.innerHTML += ' (Header)';
                    }
                    lbl.setAttribute('for', input_id);
                    d.appendChild(lbl);

                    var field = null;
                    if (field_type == 'select') {
                        field = document.createElement('select');
                        for (var i = 0; i < options.length; i++) {
                            var option = document.createElement('option');
                            option.value = options[i];
                            option.innerHTML = this.format(options[i]);
                            field.appendChild(option);
                        }
                    } else {
                        field = document.createElement('input');
                        field.type = 'text';
                    }
                    field.id = input_id;
                    field.name = name;
                    d.appendChild(field);

                    parent.appendChild(d);
                };
                pr.create_form_buttons = function(parent) {
                    var subm = document.createElement('input');
                    subm.type = 'submit';
                    subm.value = 'Execute request (' + this.method_name + ')';
                    subm.className = 'submit';
                    parent.appendChild(subm);

                    var that = this;
                    var create_field = document.createElement('a');
                    create_field.href = '#';
                    create_field.className = 'add_input';
                    create_field.innerHTML = 'Add parameter';
                    create_field.onclick = function() {
                        var name = prompt("Enter a field name:");
                        if (name !== null) {
                            that.create_form_field(that.input_container, 'param', 'text', name);
                        }
                        return false;
                    };
                    parent.appendChild(create_field);

                    var create_header = document.createElement('a');
                    create_header.href = '#';
                    create_header.className = 'add_input';
                    create_header.innerHTML = 'Add header';
                    create_header.onclick = function() {
                        var name = prompt("Enter a header name:");
                        if (name !== null) {
                            that.create_form_field(that.input_container, 'header', 'text', name);
                        }
                        return false;
                    };
                    parent.appendChild(create_header);
                };
                pr.create_result_field = function(parent) {
                    this.result_node = document.createElement('div');
                    this.result_node.className = 'result';
                    parent.appendChild(this.result_node);
                };
                pr.on_submit = function() {
                    var xhr = null;
                    var that = this;
                    this.result_node.innerHTML = 'Executing...';

                    if (window.XMLHttpRequest) {
                        xhr = new XMLHttpRequest();
                    } else if (window.ActiveXObject) {
                        xhr = new ActiveXObject("Microsoft.XMLHTTP");
                    }
                    xhr.onreadystatechange = function() {
                        if (xhr.readyState == 4) {
                            // Received
                            var data = [
                                '<h5>Status</h5>', xhr.status, ' ',
                                that.get_status(xhr.status, xhr.statusText),
                                '<h5>Response Headers</h5>',
                                that.format(xhr.getAllResponseHeaders()),
                                '<h5>Response Body</h5>',
                                that.format(xhr.responseText),
                                '(' + xhr.responseText.length + ' bytes)'
                            ];
                            that.result_node.innerHTML = '';
                            for (var i = 0; i < data.length; i++) {
                                that.result_node.innerHTML += data[i];
                            }
                        }
                    };

                    // Get parameters and fill them into path, query string and POST data
                    var input = this.get_parameters();
                    if (input['__error__']) {
                        this.result_node.innerHTML = 'ERROR: Missing data.';
                        return false;
                    }

                    var path = this.resource.path;
                    var data = '';
                    // Request parameters
                    for (param_name in this.method.parameters) {
                        var param = this.method.parameters[param_name];
                        if (param['path_param']) {
                            path = path.replace('{' + param_name + '}', input['params'][param_name]);
                        } else {
                            data += escape(param_name) + '=' + escape(input['params'][param_name]) + '&';
                        }
                    }

                    if (data === '') {
                        data = null;
                    } else if (this.method_name == 'GET' || this.method_name == 'HEAD') {
                        // Convert data to query string
                        path += '?' + data;
                        data = null;
                    }

                    xhr.open(this.method_name, path, true);
                    if (data !== null) {
                        xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                    }
                    // Request headers
                    for (header in input['headers']) {
                        xhr.setRequestHeader(header, input['headers'][header]);
                    }
                    xhr.send(data); 

                    return false;
                };
                pr.format = function(str) {
                    var str = str.replace(/&/g, "&amp;").replace(/</g, "&lt;").
                        replace(/>/g, "&gt;");
                    // Linkify HTTP URLs
                    str = str.replace(/(http:\/\/[^ ]+)/g, '<a href="$1" target="_blank">$1</a>');
                    str = '<pre>' + str + '</pre>';
                    return str;
                };
                pr.get_status = function(status, statusText) {
                    /* Need to get the status text manually as statusText is broken on
                       Safari. */
                    if (statusText == 'OK') {
                        // Safari always uses OK, replace it manually
                        var STATI = { 200: 'OK', 201: 'Created', 202: 'Accepted',
                            203: 'Non-Authoritative Information', 204: 'No Content',
                            205: 'Reset Content', 206: 'Partial Content',
                            300: 'Multiple Choices', 301: 'Moved Permanently', 302: 'Found',
                            303: 'See Other', 304: 'Not Modified', 305: 'Use Proxy',
                            307: 'Temporary Redirect', 400: 'Bad Request',
                            401: 'Unauthorized', 402: 'Payment Required', 403: 'Forbidden',
                            404: 'Not Found', 405: 'Method Not Allowed', 406: 'Not Acceptable',
                            407: 'Proxy Authentication Required', 408: 'Request Timeout',
                            409: 'Conflict', 410: 'Gone', 411: 'Length Required',
                            412: 'Precondition Failed', 413: 'Request Entity Too Large',
                            414: 'Request-URI Too Long', 415: 'Unsupported Media Type',
                            416: 'Requested Range Not Satisfiable', 417: 'Expectation Failed',
                            500: 'Internal Server Error', 501: 'Not Implemented',
                            502: 'Bad Gateway', 503: 'Service Unavailable',
                            504: 'Gateway Timeout', 505: 'HTTP Version Not Supported'
                        };
                        if (typeof(STATI[status]) !== 'undefined') {
                            return STATI[status];
                        }
                    }
                    return statusText;
                };
                pr.get_parameters = function() {
                    var params = {'__error__': false, 'headers': {}, 'params': {}};
                    var fields = [];

                    // Get all fields
                    var inputs = this.target.getElementsByTagName('input');
                    for (var i = 0; i < inputs.length; i++) {
                        fields.push(inputs[i]);
                    }
                    var selects = this.target.getElementsByTagName('select');
                    for (var i = 0; i < selects.length; i++) {
                        fields.push(selects[i]);
                    }


                    var inp = null;
                    for (var i = 0; i < fields.length; i++) {
                        inp = fields[i];
                        var type = inp.parentNode.className;
                        if (type == 'header') {
                            params['headers'][inp.name] = inp.value;
                        } else if (type == 'param') {
                            inp.className = '';
                            params['params'][inp.name] = inp.value;

                            // Validate input
                            if (this.method.parameters[inp.name]['mandatory'] && inp.value === '') {
                                inp.className = 'error';
                                params['__error__'] = true;
                            }
                        }
                    }
                    return params;
                };

                /* Hides all .resource_details elements and inserts a toggle link at their
                   place. */
                function toggle_visibility() {
                    var divs = document.getElementsByTagName('div');
                    var len = divs.length;
                    for (var i = 0; i < len; i++) {
                        var div = divs[i];
                        if (div.className == 'method_details') {
                            toggle_visibility_div(div);
                        }
                    }
                }

                function toggle_visibility_div(div) {
                    div.className += ' hidden';
                    var link = document.createElement('a');
                    link.innerHTML = 'Show details';
                    link.href = '#';
                    link.className = 'toggle_details';
                    link.onclick = function() {
                        console.debug(div);
                        if (link.innerHTML == 'Show details') {
                            div.className = div.className.replace(' hidden', '');
                            link.innerHTML = 'Hide details';
                        } else {
                            div.className += ' hidden';
                            link.innerHTML = 'Show details';
                        }
                        return false;
                    };
                    div.parentNode.insertBefore(link, div);
                }
                </script>
            </head>
            <body>
                <h1>WsgiService help</h1>
        """]
        self.to_text_html_overview(retval, raw)
        self.to_text_html_resources(retval, raw)
        retval.append('<script>toggle_visibility();</script>')
        retval.append('</body></html>')
        return re.compile('^ *', re.MULTILINE).sub('', "".join(retval))

    def to_text_html_overview(self, retval, raw):
        """Add the overview table to the HTML output."""
        retval.append('<table id="overview">')
        retval.append('<tr><th>Resource</th><th>Path</th><th>Description</th></tr>')
        for resource in raw:
            retval.append('<tr><td><a href="#{0}">{0}</a></td><td>{1}</td><td>{2}</td></tr>'.format(
                xml_escape(resource['name']), xml_escape(resource['path']),
                xml_escape(resource['desc'])))
        retval.append('</table>')

    def to_text_html_resources(self, retval, raw):
        """Add the resources details to the HTML output."""
        for resource in raw:
            retval.append('<div class="resource_details">')
            retval.append('<h2 id="{0}">{0}</h2>'.format(
                xml_escape(resource['name'])))
            if resource['desc']:
                retval.append('<p class="desc">{0}</p>'.format(xml_escape(resource['desc'])))
            retval.append('<table class="config">')
            retval.append('<tr><th>Path</th><td>{0}</td>'.format(xml_escape(
                resource['path'])))
            representations = [value + ' (.' + key + ')' for key, value
                in resource['properties']['EXTENSION_MAP'].iteritems()]
            retval.append('<tr><th>Representations</th><td>{0}</td>'.format(
                xml_escape(', '.join(representations))))
            retval.append('</table>')
            self.to_text_html_methods(retval, resource)
            retval.append('</div>')
    
    def to_text_html_methods(self, retval, resource):
        """Add the methods of this resource to the HTML output."""
        for method_name, method in resource['methods'].iteritems():
            retval.append('<h3 id="{0}_{1}">{1}</h3>'.format(
                xml_escape(resource['name']), xml_escape(method_name)))
            retval.append('<div class="method_details" id="{0}_{1}_container">'.format(
                xml_escape(resource['name']), xml_escape(method_name)))
            if method['desc']:
                retval.append('<p class="desc">{0}</p>'.format(xml_escape(method['desc'])))
            if method['parameters']:
                retval.append('<table class="parameters">')
                retval.append('<tr><th>Name</th><th>Mandatory</th><th>Description</th><th>Validation</th>')
                for param_name, param in method['parameters'].iteritems():
                    mandatory = '-'
                    description = param['desc']
                    validation = ''
                    if param['mandatory']:
                        mandatory = 'Yes'
                    if param['path_param']:
                        mandatory += ' (Path parameter)'
                    if param['validate_re']:
                        validation = 'Regular expression: <tt>' + \
                            xml_escape(param['validate_re']) + '</tt>'
                    retval.append('<tr><td>{0}</td><td>{1}</td><td>{2}</td>'
                        '<td>{3}</td>'.format(xml_escape(param_name),
                        xml_escape(mandatory), xml_escape(description), validation))
                retval.append('</table>')
            retval.append('</div>')
            retval.append('<script>add_resource_method({0},{1},{2},{3});</script>'.format(
                xml_escape(json.dumps(resource['name']+'_'+method_name+'_container')),
                xml_escape(json.dumps(resource)),
                xml_escape(json.dumps(method_name)),
                xml_escape(json.dumps(method))))

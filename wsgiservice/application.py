"""Components responsible for building the WSGI application."""
import hashlib
import inspect
import logging
import re
import webob
import wsgiservice
from wsgiservice.exceptions import ValidationException
from wsgiservice.status import *

logger = logging.getLogger(__name__)

class Application(object):
    """WSGI application wrapping a set of WsgiService resources. This class
    can be used as a WSGI application according to :pep:`333`.

    :param resources: A list of :class:`wsgiservice.Resource` classes to be
                      served by this application.

    .. todo:: Think about how to handle 201, 200/204 methods.
    .. todo:: Make downtime configurable with a file or something like that?
       Could then send out a 503 response with proper Retry-After header.
    .. todo:: Allow easy pluggin in of a compression WSGI middleware
    .. todo:: Convert to requested charset with Accept-Charset header
    .. todo:: Return Allow header as response to PUT and for 405 (also 501?)
    .. todo:: Implement Content-Location header
    .. todo:: Log From and Referer headers
    .. todo:: On 201 created provide Location header
    .. todo:: Abstract away error and status code handling
    .. todo:: Easy deployment using good configuration file handling
    .. todo:: Create usable REST API documentation from source
    .. todo:: Support OPTIONS, send out the Allow header, and some
       machine-readable output in the correct format. ``OPTIONS *`` can be
       discarded as NOOP
    .. todo:: Must return different ETags for different representations of a
       resource.
    """
    def __init__(self, resources):
        self._resources = resources
        self._urlmap = wsgiservice.routing.Router(resources)
    
    def __call__(self, environ, start_response):
        """WSGI entry point. Serve the best matching resource for the current
        request.
        """
        request = webob.Request(environ)
        response = self._handle_request(request)
        return response(environ, start_response)
    
    def _handle_request(self, request):
        """Finds the resource to which a request maps and then calls it.
        Instantiates and returns a :class:`webob.Response` object."""
        response = webob.Response()
        path = request.path_info
        parsed = self._urlmap(path)
        if not parsed:
            response.status = 404
            return response
        path_params, resource = parsed
        response = self._call_resource(resource, path_params, request, response)
        if request.method == 'HEAD':
            response.body = ''
        return response
    
    def _call_resource(self, resource, path_params, request, response):
        """Executes the request on the given resource. Resolves the method
        name to a Python methods, checks all preconditions and it everything
        is okay, actually calls the Python method.
        """
        instance = resource(request, response, path_params)
        method = None
        try:
            method = self._resolve_method(instance, instance.request.method)
            self._handle_conditions(instance)
            self._call_method(instance, method)
        except ResponseException, e:
            # a response was raised, catch it
            instance.response = e.response
        self._convert_response(instance, method)
        return response
    
    def _resolve_method(self, instance, method):
        """Tries to find a Python method on the given instance which can be
        used for the given HTTP method. Raises a HTTP exception if no method
        exists.
        """
        if hasattr(instance, method) and callable(getattr(instance, method)):
            return method
        elif method == 'HEAD':
            return self._resolve_method(instance, 'GET')
        # Error: did not find any method, raise a 405 or 501 exception
        elif instance.request.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT',
                              'DELETE', 'TRACE', 'CONNECT'):
            # Known HTTP methods => 405 Method Not Allowed
            raise_405(instance)
        else:
            # Unknown HTTP methods => 501 Not Implemented
            raise_501(instance)
    
    def _handle_conditions(self, instance):
        """Handles various HTTP conditions and can raise HTTP exceptions to
        abort the request.
        
            - Content-MD5 request header must match the MD5 hash of the full
              input.
        """
        if 'Content-MD5' in instance.request.headers:
            body_md5 = hashlib.md5(instance.request.body_file.read()).hexdigest()
            if body_md5 != instance.request.headers['Content-MD5']:
                raise_400(instance, msg='The Content-MD5 request header does not match the body.')
        instance.response.etag = self._get_etag(instance)
        instance.response.last_modified = self._get_last_modified(instance)
        self._handle_condition_etag(instance)
        self._handle_condition_last_modified(instance)
    
    def _handle_condition_etag(self, instance):
        if instance.response.etag:
            etag = instance.response.etag.replace('"', '')
            if not etag in instance.request.if_match:
                raise_412(instance)
            if etag in instance.request.if_none_match:
                if instance.request.method in ('GET', 'HEAD'):
                    raise_304(instance)
                else:
                    raise_412(instance)
    
    def _handle_condition_last_modified(self, instance):
        rq = instance.request
        rs = instance.response
        if rs.last_modified:
            if rq.if_modified_since and rs.last_modified <= rq.if_modified_since:
                raise_304(instance)
            if rq.if_unmodified_since and rs.last_modified > rq.if_unmodified_since:
                raise_412(instance)
    
    def _call_method(self, instance, method):
        instance.response.body_raw = self._call_dynamic_method(instance, method)
    
    def _convert_response(self, instance, method):
        """Finish filling the webob.Response object so it's ready to be
        served to the client. This includes converting the body_raw property
        to the content type requested by the user if necessary.
        """
        rs = instance.response
        rq = instance.request
        extension_map = { '.xml': 'text/xml', '.json': 'application/json'}
        available_types = ['text/xml', 'application/json']
        extension = instance.path_params.get('_extension')
        if extension in extension_map:
            out_type = extension_map[extension]
        else:
            out_type = rq.accept.first_match(available_types)
        if hasattr(rs, 'body_raw'):
            if rs.body_raw is not None:
                to_type = re.sub('[^a-zA-Z_]', '_', out_type)
                to_type_method = 'to_' + to_type
                if hasattr(instance, to_type_method):
                    getattr(instance, to_type_method)(rs.body_raw)
            rs.headers['Content-Type'] = out_type + '; charset=UTF-8'
            del rs.body_raw
        if extension in extension_map:
            # Used the Accept headers to very response
            if rs.vary is None:
                rs.vary = ['Accept']
            else:
                rs.vary.append('Accept')
        rs.content_md5 = hashlib.md5(rs.body).hexdigest()
    
    def _get_etag(self, instance):
        retval = self._call_dynamic_method(instance, 'get_etag')
        if retval:
            return '"' + retval.replace('"', '') + '"'
    
    def _get_last_modified(self, instance):
        return self._call_dynamic_method(instance, 'get_last_modified')
    
    def _call_dynamic_method(self, instance, method):
        """Call an instance method replacing all the parameter names. The
        parameters are filled in from the following locations (in that order
        of precedence):
            1. Path parameters from routing
            2. GET parameters
            3. POST parameters
        The value of the method is then returned.
        """
        method = getattr(instance, method)
        method_params, varargs, varkw, defaults = inspect.getargspec(method)
        if method_params:
            method_params.pop(0) # pop the self off
        params = []
        request = instance.request
        for param in method_params:
            value = None
            if param in instance.path_params:
                value = instance.path_params[param]
            elif param in request.GET:
                value = request.GET[param]
            elif param in request.POST:
                value = request.POST[param]
            self._validate_param(method, param, value)
            params.append(value)
        return method(*params)
    
    def _validate_param(self, method, param, value):
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
        if rules is None:
            return
        if value is None or len(value) == 0:
            raise ValidationException("Value for {0} must not be empty.".format(param))
        elif 're' in rules and rules['re']:
            if not re.search('^' + rules['re'] + '$', value):
                raise ValidationException("{0} value {1} does not validate.".format(param, value))
    

def get_app(defs):
    """Small wrapper function to returns an instance of :class:`Application`
    which serves the objects in the defs. Usually this is called with return
    value globals() from the module where the resources are defined. The
    returned WSGI application will serve all subclasses of
    :class:`wsgiservice.Resource` found in the dictionary.

    :param defs: Each :class:`wsgiservice.Resource` object found in the values
                 of this dictionary is used as application resource. The other
                 values are discarded.
    :type defs: dict
    :rtype: :class:`Application`
    """
    if isinstance(defs, tuple):
        # A list of different applications mounted at different paths
        # TODO
        defs = defs[1]
    resources = [d for d in defs.values() if d in wsgiservice.Resource.__subclasses__()]
    return Application(resources)

"""Components responsible for building the WSGI application."""
import re
import wsgiservice
import inspect
from wsgiservice import Response
from wsgiservice.objects import MiniResponse
from wsgiservice.exceptions import ValidationException

class Application(object):
    """WSGI application wrapping a set of WsgiService resources."""
    def __init__(self, resources):
        self._resources = resources
        self._urlmap = wsgiservice.routing.Router(resources)

    def __call__(self, environ, start_response):
        # Find the correct resource
        res = self._handle_request(environ)
        if isinstance(res, Response):
            b = str(res)
            start_response(res.status, res.headers)
            return b

    def _handle_request(self, environ):
        path = environ['PATH_INFO']
        parsed = self._urlmap(path)
        if not parsed:
            return Response({'error': 'not found'}, environ, status=404)
        else:
            path_params, res = parsed
            return self._call_resource(res, path_params, environ)

    def _call_resource(self, res, path_params, environ):
        request = wsgiservice.Request(environ)
        instance = res()
        method = self._resolve_method(instance, request.method)
        if not method:
            return self._get_response_405(instance, environ)
        etag = self._get_etag(instance, path_params, request)
        if etag:
            etag_match = etag.replace('"', '')
            if not etag_match in request.if_match:
                return self._get_response_412(etag, instance, environ)
            if etag_match in request.if_none_match:
                if request.method == 'GET':
                    return self._get_response_304(etag, instance, environ)
                else:
                    return self._get_response_412(etag, instance, environ)
        body, headers = self._call_dynamic_method(instance, method,
            path_params, request), None
        if isinstance(body, MiniResponse):
            body, headers = body.body, body.headers
        if etag:
            headers['ETag'] = etag
        return Response(body, environ, instance, method,
            headers =headers,
            extension=path_params.get('_extension', None))

    def _resolve_method(self, instance, method):
        if hasattr(instance, method) and callable(getattr(instance, method)):
            return method
        elif method == 'HEAD':
            return self._resolve_method(instance, 'GET')
        return None

    def _get_response_304(self, etag, instance, environ):
        headers = {}
        if etag:
            headers['ETag'] = etag
        return Response(None, environ, instance, status=304, headers=headers)

    def _get_response_405(self, instance, environ):
        methods = [method for method in dir(instance)
            if method.upper() == method
            and callable(getattr(instance, method))]
        return Response({'error': 'Invalid method on resource'}, environ,
            instance, status=405, headers={'Allow': ", ".join(methods)})

    def _get_response_412(self, etag, instance, environ):
        headers = {}
        if etag:
            headers['ETag'] = etag
        return Response({'error': 'Precondition failed.'}, environ,
            instance, status=412, headers=headers)

    def _get_etag(self, instance, path_params, request):
        if not hasattr(instance, 'get_etag'):
            return None
        retval = self._call_dynamic_method(instance, 'get_etag', path_params,
            request)
        if retval:
            return '"' + retval.replace('"', '') + '"'

    def _call_dynamic_method(self, instance, method, path_params, request):
        method = getattr(instance, method)
        method_params, varargs, varkw, defaults = inspect.getargspec(method)
        if method_params:
            method_params.pop(0) # pop the self off
        params = []
        for param in method_params:
            value = None
            if param == 'request':
                value = request
            elif param in path_params:
                value = path_params[param]
            elif param in request.GET:
                value = request.GET[param]
            elif param in request.POST:
                value = request.POST[param]
            self._validate_param(method, param, value)
            params.append(value)
        return method(*params)

    def _validate_param(self, method, param, value):
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
    """Returns a WSGI app which serves the objects in the defs. Usually this
    is called with return value globals() from the module where the resources
    are defined. The returned WSGI application will serve all subclasses of
    Resource.
    """
    if isinstance(defs, tuple):
        # A list of different applications mounted at different paths
        # TODO
        defs = defs[1]
    resources = [d for d in defs.values() if d in wsgiservice.Resource.__subclasses__()]
    return Application(resources)

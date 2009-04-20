"""Components responsible for building the WSGI application."""
import wsgiservice
from wsgiservice import Response

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
        method = environ['REQUEST_METHOD']
        instance = res()
        if hasattr(instance, method) and callable(getattr(instance, method)):
            method = getattr(instance, method)
            method_params = method.func_code.co_varnames[1:method.func_code.co_argcount]
            params = []
            request = wsgiservice.Request(environ)
            for param in method_params:
                value = None
                if param == 'request':
                    value = request
                elif param in path_params:
                    value = path_params[param]
                elif param in request.POST:
                    value = request.POST[param]
                self._validate_param(method, param, value)
                params.append(value)
            response = method(*params)
            return Response(response, environ, instance, method,
                extension=path_params.get('_extension', None))
        else:
            methods = [method for method in dir(instance)
                if method.upper() == method
                and callable(getattr(instance, method))]
            return Response({'error': 'Invalid method on resource'}, environ,
                instance, status=405, headers={'Allow': ", ".join(methods)})

    def _validate_param(self, method, param, value):
        rules = None
        if hasattr(method, '_validations') and param in method._validations:
            rules = method._validations[param]
        elif hasattr(method.im_class, '_validations') and param in method.im_class._validations:
            rules = method.im_class._validations[param]
        if rules is None:
            return
        if 're' in rules and rules['re']:
            if not re.search('^' + rules['re'] + '$', value):
                raise Exception("{0} value {1} does not validate.".format(param, value))
        elif value is None or len(value) == 0:
            raise Exception("Value for {0} must not be empty.".format(param))

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

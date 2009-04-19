"""WsgiService module containing all the root level definitions."""
import cgi
import functools
import json
import re

class Router(object):
    def __init__(self, resources):
        self._routes = []
        search_vars = re.compile(r'\{(\w+)\}').finditer
        for res in resources:
            # Compile regular expression for each path
            path, regexp, prev_pos = res._path, '^', 0
            for match in search_vars(path):
                regexp += re.escape(path[prev_pos:match.start()])
                regexp += '(?P<{0}>.+)'.format(match.group(1))
                prev_pos = match.end()
            regexp += re.escape(path[prev_pos:])
            regexp += '$'
            self._routes.append((re.compile(regexp).match, res))

    def __call__(self, path):
        for match, res in self._routes:
            retval = match(path)
            if retval:
                return (retval.groupdict(), res)


class Response(object):
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

    def __init__(self, body, environ, resource=None, headers=None, status=200):
        self._environ = environ
        self._resource = resource
        self._body = body
        self._headers = {'Content-type': 'text/xml'}
        if headers:
            for key in headers:
                self._headers[key] = headers[key]
        self.status = self._status_map[status]

    @property
    def headers(self):
        return self._headers.items()

    def __str__(self):
        return json.dumps(self._body)


class Request(object):
    def __init__(self, environ):
        self.POST = cgi.FieldStorage(fp=environ['wsgi.input'],
            environ=environ, keep_blank_values=1)


class Application(object):
    """WSGI application wrapping a set of WsgiService resources."""
    def __init__(self, resources):
        self._resources = resources
        self._urlmap = Router(resources)

    def __call__(self, environ, start_response):
        # Find the correct resource
        res = self._handle_request(environ)
        if isinstance(res, Response):
            b = str(res)
            start_response(res.status, res.headers)
            return b

    def _handle_request(self, environ):
        path = environ['PATH_INFO']
        path_params, res = self._urlmap(path)
        if not res:
            return Response({'error': 'not found'}, environ, status=404)
        else:
            return self._call_resource(res, path_params, environ)

    def _call_resource(self, res, path_params, environ):
        method = environ['REQUEST_METHOD']
        instance = res()
        if hasattr(instance, method) and callable(getattr(instance, method)):
            method = getattr(instance, method)
            method_params = method.func_code.co_varnames[1:method.func_code.co_argcount]
            params = []
            request = Request(environ)
            for param in method_params:
                if param == 'request':
                    params.append(request)
                elif param in path_params:
                    params.append(path_params[param])
                elif param in request.POST:
                    params.append(request.POST[param])
            response = method(*params)
            return Response(response, environ, instance)
        else:
            methods = [method for method in dir(instance)
                if method.upper() == method
                and callable(getattr(instance, method))]
            return Response('Invalid method on resource', environ, instance,
                status=405, headers={'Allow': ", ".join(methods)})


def mount(path):
    "Mounts a Resource at the given path."
    def wrap(cls):
        cls._path = path
        return cls
    return wrap

def get_app(defs):
    """Returns a WSGI app which serves the objects in the defs. Usually this
    is called with return value globals() from the module where the resources
    are defined. The returned WSGI application will serve all subclasses of
    Resource.
    """
    resources = [d for d in defs.values() if d in Resource.__subclasses__()]
    return Application(resources)

class Resource(object):
    """Base class for all WsgiService resources. A resourse is a unique REST
    endpoint which accepts different methods for different actions."""


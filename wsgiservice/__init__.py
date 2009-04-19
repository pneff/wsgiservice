"""WsgiService module containing all the root level definitions."""
import re
import functools
import routes.base

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
            if match(path):
                return res


class Application(object):
    """WSGI application wrapping a set of WsgiService resources."""
    def __init__(self, resources):
        self._resources = resources
        self._urlmap = Router(resources)

    def __call__(self, environ, start_response):
        # Find the correct resource
        path = environ['PATH_INFO']
        res = self._urlmap(path)
        if not res:
            status = '404 Not Found'
            headers = [('Content-type', 'text/xml')]
            start_response(status, headers)
            return "<error>not found</error>"
        else:
            return self._call_resource(res, environ, start_response)

    def _call_resource(self, res, environ, start_response):
        method = environ['REQUEST_METHOD']
        instance = res()
        if hasattr(instance, method) and callable(getattr(instance, method)):
            status = '200 OK'
            headers = [('Content-type', 'text/xml')]
            start_response(status, headers)
            return "Resource can be called with {0}".format(method)
        else:
            status = '405 Method Not Allowed'
            headers = [('Content-type', 'text/xml')]
            start_response(status, headers)
            return "<error>invalid method on resource</error>"


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


"""Components responsible for building the WSGI application."""
import inspect
import logging
import webob
import wsgiservice
import wsgiservice.resource

logger = logging.getLogger(__name__)

class Application(object):
    """WSGI application wrapping a set of WsgiService resources. This class
    can be used as a WSGI application according to :pep:`333`.

    :param resources: A list of :class:`wsgiservice.Resource` classes to be
                      served by this application.

    :var LOG_DATA: A list of request attributes to log. Each of these must be
        a valid attribute name of a :class:`webob.Request` instance and is
        included in the log output if it's non-empty. (Default: ['url',
        'remote_user', 'remote_addr', 'referer'])

    :var LOG_HEADERS: A list of request headers to log. Each of these is
        logged if it was sent by the client and is non-empty. (Default:
        ['From'])

    .. todo:: Make downtime configurable with a file or something like that?
       Could then send out a 503 response with proper Retry-After header.
    .. todo:: Convert to requested charset with Accept-Charset header
    .. todo:: Easy deployment using good configuration file handling
    .. todo:: Create usable REST API documentation from source
    """
    LOG_DATA = ['url', 'remote_user', 'remote_addr', 'referer']
    LOG_HEADERS = ['From']

    def __init__(self, resources):
        self._resources = resources
        self._urlmap = wsgiservice.routing.Router(resources)
    
    def __call__(self, environ, start_response):
        """WSGI entry point. Serve the best matching resource for the current
        request.
        """
        request = webob.Request(environ)
        self._log_request(request)
        response = self._handle_request(request)
        return response(environ, start_response)
    
    def _log_request(self, request):
        """Log the most important parts of this request."""
        msg = []
        for d in self.LOG_DATA:
            val = getattr(request, d)
            if val:
                msg.append(d + ': ' + repr(val))
        for d in self.LOG_HEADERS:
            if d in request.headers and request.headers[d]:
                msg.append(d + ': ' + repr(request.headers[d]))
        logger.info(', '.join(msg))
    
    def _handle_request(self, request):
        """Finds the resource to which a request maps and then calls it.
        Instantiates and returns a :class:`webob.Response` object."""
        response = webob.Response(request=request)
        path = request.path_info
        parsed = self._urlmap(path)
        if not parsed:
            response.status = 404
            return response
        path_params, resource = parsed
        instance = resource(request=request, response=response,
            path_params=path_params, application=self)
        response = instance()
        if request.method == 'HEAD':
            response.body = ''
        return response


def get_app(defs, add_help=True):
    """Small wrapper function to returns an instance of :class:`Application`
    which serves the objects in the defs. Usually this is called with return
    value globals() from the module where the resources are defined. The
    returned WSGI application will serve all subclasses of
    :class:`wsgiservice.Resource` found in the dictionary.

    :param defs: Each :class:`wsgiservice.Resource` object found in the values
                 of this dictionary is used as application resource. The other
                 values are discarded.
    :type defs: dict
    :param add_help: Wether to add the Help resource which will expose the
                     documentation of this service at /_internal/help
    :type add_help: boolean
    :rtype: :class:`Application`
    """
    resources = [d for d in defs.values() if inspect.isclass(d) and
        issubclass(d, wsgiservice.Resource) and hasattr(d, '_path')]
    if add_help:
        resources.append(wsgiservice.resource.Help)
    return Application(resources)

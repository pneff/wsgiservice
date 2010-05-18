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

    .. todo:: Easy deployment using good configuration file handling
    """

    #: A list of request attributes to log. Each of these must be a valid
    #: attribute name of a :class:`webob.Request` instance and is included in
    #: the log output if it's non-empty. (Default: ['url', 'remote_user',
    #: 'remote_addr', 'referer'])
    LOG_DATA = ['url', 'remote_user', 'remote_addr', 'referer']

    #: A list of request headers to log. Each of these is logged if it was sent by
    #: the client and is non-empty. (Default: ['From'])
    LOG_HEADERS = ['From']

    #: :class:`wsgiservice.resource.Resource` class. Used as the default
    #: resource when the routing does not return any match.
    NOT_FOUND_RESOURCE = wsgiservice.resource.NotFoundResource

    #: Resource classes served by this application. Set by the constructor.
    _resources = None

    #: :class:`wsgiservice.routing.Router` instance. Set by the constructor.
    _urlmap = None

    def __init__(self, resources):
        """Constructor.

        :param resources: List of :class:`wsgiservice.resource.Resource`
                          classes to be served by this application.
        """
        self._resources = resources
        self._urlmap = wsgiservice.routing.Router(resources)

    def __call__(self, environ, start_response):
        """WSGI entry point. Serve the best matching resource for the current
        request. See :pep:`333` for details of this method.

        :param environ: Environment dictionary.
        :param start_response: Function called when the response is ready to
               be served.
        """
        request = webob.Request(environ)
        self._log_request(request)
        response = self._handle_request(request)
        return response(environ, start_response)

    def _log_request(self, request):
        """Log the most important parts of this request.

        :param request: Object representing the current request.
        :type request: :class:`webob.Request`
        """
        msg = []
        for d in self.LOG_DATA:
            val = getattr(request, d)
            if val:
                msg.append(d + ': ' + repr(val))
        for d in self.LOG_HEADERS:
            if d in request.headers and request.headers[d]:
                msg.append(d + ': ' + repr(request.headers[d]))
        logger.info("Reqest information: %s", ', '.join(msg))

    def _handle_request(self, request):
        """Finds the resource to which a request maps and then calls it.
        Instantiates, fills and returns a :class:`webob.Response` object. If
        no resource matches the request, a 404 status is set on the responrce
        object.

        :param request: Object representing the current request.
        :type request: :class:`webob.Request`
        """
        response = webob.Response(request=request)
        path = request.path_info
        parsed = self._urlmap(path)
        if parsed:
            path_params, resource = parsed
        else:
            path_params, resource = {}, self.NOT_FOUND_RESOURCE
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
    def is_resource(d):
        try:
            if issubclass(d, wsgiservice.Resource) and hasattr(d, '_path'):
                return True
        except TypeError:
            pass # d wasn't a class
            
        return False
    
    resources = [d for d in defs.values() if is_resource(d)]
    if add_help:
        resources.append(wsgiservice.resource.Help)
    return Application(resources)

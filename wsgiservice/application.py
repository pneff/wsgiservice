"""Components responsible for building the WSGI application."""
import logging
import webob
import wsgiservice

logger = logging.getLogger(__name__)

class Application(object):
    """WSGI application wrapping a set of WsgiService resources. This class
    can be used as a WSGI application according to :pep:`333`.

    :param resources: A list of :class:`wsgiservice.Resource` classes to be
                      served by this application.

    .. todo:: Make downtime configurable with a file or something like that?
       Could then send out a 503 response with proper Retry-After header.
    .. todo:: Convert to requested charset with Accept-Charset header
    .. todo:: Return Allow header as response to PUT and for 405 (also 501?)
    .. todo:: Log From and Referer headers
    .. todo:: Abstract away error and status code handling
    .. todo:: Easy deployment using good configuration file handling
    .. todo:: Create usable REST API documentation from source
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
        response = webob.Response(request=request)
        path = request.path_info
        parsed = self._urlmap(path)
        if not parsed:
            response.status = 404
            return response
        path_params, resource = parsed
        response = resource(request, response, path_params).call()
        if request.method == 'HEAD':
            response.body = ''
        return response


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

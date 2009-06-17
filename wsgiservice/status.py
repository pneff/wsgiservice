"""Helper methods to raise responses for the various HTTP status codes."""
from urlparse import urljoin

class ResponseException(Exception):
    """Wraps a :class:`webob.Response` object to be thrown as an exception."""
    def __init__(self, response):
        self.response = response

def raise_201(instance, location):
    """Abort the current request with a 201 (Created) response code. Sets the
    Location header correctly. If the location does not start with a slash,
    the path of the current request is prepended.
    """
    if not location.startswith('/'):
        location = urljoin(instance.request.path.rstrip('/') + '/', location)
    instance.response.location = location
    instance.response.status = 201
    raise ResponseException(instance.response)

def raise_204(instance):
    """Abort the current request with a 204 (No Content) response code. Clears
    out the body of the response.
    """
    instance.response.status = 204
    instance.response.body = ''
    instance.response.body_raw = None
    raise ResponseException(instance.response)

def raise_304(instance):
    """Abort the current request with a 304 (Not Modified) response code."""
    instance.response.status = 304
    raise ResponseException(instance.response)

def raise_400(instance, msg=None):
    """Abort the current request with a 400 (Bad Request) response code. If
    the message is given it's output as the response body (correctly converted
    to the requested MIME type).
    """
    instance.response.status = 400
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)

def raise_404(instance):
    """Abort the current request with a 404 (Not Found) response code."""
    instance.response.status = 404
    raise ResponseException(instance.response)

def raise_405(instance):
    """Abort the current request with a 405 (Method Not Allowed) response
    code."""
    instance.response.status = 405
    instance.response.headers['Allow'] = instance.get_allowed_methods()
    raise ResponseException(instance.response)

def raise_412(instance):
    """Abort the current request with a 412 (Precondition Failed) response
    code."""
    instance.response.status = 412
    raise ResponseException(instance.response)

def raise_501(instance):
    """Abort the current request with a 501 (Not Implemented) response
    code."""
    instance.response.status = 501
    instance.response.headers['Allow'] = instance.get_allowed_methods()
    raise ResponseException(instance.response)

"""Helper methods to raise responses for the various HTTP status codes.

The motivation for these methods is to be able to easily document the HTTP
response headers which are highly recommended or required. For example the
``Location`` header which should be set for 201 responses.

The following status codes don't have a method here:
"""
from urlparse import urljoin
from wsgiservice.exceptions import ResponseException


def raise_200(instance):
    """Abort the current request with a 200 (OK) response code.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 200
    """
    instance.response.status = 200
    raise ResponseException(instance.response)


def raise_201(instance, location):
    """Abort the current request with a 201 (Created) response code. Sets the
    Location header correctly. If the location does not start with a slash,
    the path of the current request is prepended.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 201
    """
    _set_location(instance, location)
    instance.response.status = 201
    raise ResponseException(instance.response)


def raise_202(instance):
    """Abort the current request with a 202 (Accepted) response code.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 202
    """
    instance.response.status = 202
    raise ResponseException(instance.response)


def raise_204(instance):
    """Abort the current request with a 204 (No Content) response code. Clears
    out the body of the response.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 204
    """
    instance.response.status = 204
    instance.response.body = ''
    instance.response.body_raw = None
    raise ResponseException(instance.response)


def raise_205(instance):
    """Abort the current request with a 205 (Reset Content) response code.
    Clears out the body of the response.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 205
    """
    instance.response.status = 205
    instance.response.body = ''
    instance.response.body_raw = None
    raise ResponseException(instance.response)


def raise_300(instance):
    """Abort the current request with a 300 (Multiple Choices) response code.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 300
    """
    instance.response.status = 300
    raise ResponseException(instance.response)


def raise_301(instance, location):
    """Abort the current request with a 301 (Moved Permanently) response code.
    Sets the Location header correctly. If the location does not start with a
    slash, the path of the current request is prepended.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 301
    """
    _set_location(instance, location)
    instance.response.status = 301
    raise ResponseException(instance.response)


def raise_302(instance, location):
    """Abort the current request with a 302 (Found) response code. Sets the
    Location header correctly. If the location does not start with a slash,
    the path of the current request is prepended.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 302
    """
    _set_location(instance, location)
    instance.response.status = 302
    raise ResponseException(instance.response)


def raise_303(instance, location):
    """Abort the current request with a 303 (See Other) response code. Sets
    the Location header correctly. If the location does not start with a
    slash, the path of the current request is prepended.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 303
    """
    _set_location(instance, location)
    instance.response.status = 303
    raise ResponseException(instance.response)


def raise_304(instance):
    """Abort the current request with a 304 (Not Modified) response code.
    Clears out the body of the response.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 304

    .. todo: The following headers MUST be output: Date, ETag and/or
             Content-Location, Expires, Cache-Control, Vary. See :rfc:`2616`
             section 10.3.5.
    """
    instance.response.status = 304
    instance.response.body = ''
    instance.response.body_raw = None
    raise ResponseException(instance.response)


def raise_305(instance, location):
    """Abort the current request with a 305 (Use Proxy) response code. Sets
    the Location header correctly. If the location does not start with a
    slash, the path of the current request is prepended.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 305
    """
    _set_location(instance, location)
    instance.response.status = 305
    raise ResponseException(instance.response)


def raise_307(instance, location):
    """Abort the current request with a 307 (Temporary Redirect) response
    code. Sets the Location header correctly. If the location does not start
    with a slash, the path of the current request is prepended.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 307
    """
    _set_location(instance, location)
    instance.response.status = 307
    raise ResponseException(instance.response)


def raise_400(instance, msg=None):
    """Abort the current request with a 400 (Bad Request) response code. If
    the message is given it's output as an error message in the response body
    (correctly converted to the requested MIME type).

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 400
    """
    instance.response.status = 400
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)


def raise_401(instance, authenticate, msg=None):
    """Abort the current request with a 401 (Unauthorized) response code. If
    the message is given it's output as an error message in the response body
    (correctly converted to the requested MIME type). Outputs the
    WWW-Authenticate header as given by the authenticate parameter.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 401
    """
    instance.response.status = 401
    instance.response.headers['WWW-Authenticate'] = authenticate
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)


def raise_402(instance, msg=None):
    """Abort the current request with a 402 (Payment Required) response code.
    If the message is given it's output as an error message in the response
    body (correctly converted to the requested MIME type).

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 402
    """
    instance.response.status = 402
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)


def raise_403(instance, msg=None):
    """Abort the current request with a 403 (Forbidden) response code. If the
    message is given it's output as an error message in the response body
    (correctly converted to the requested MIME type).

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 403
    """
    instance.response.status = 403
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)


def raise_404(instance):
    """Abort the current request with a 404 (Not Found) response code.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 404
    """
    instance.response.status = 404
    raise ResponseException(instance.response)


def raise_405(instance):
    """Abort the current request with a 405 (Method Not Allowed) response
    code. Sets the ``Allow`` response header to the return value of the
    :func:`Resource.get_allowed_methods` function.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 405
    """
    instance.response.status = 405
    instance.response.headers['Allow'] = instance.get_allowed_methods()
    raise ResponseException(instance.response)


def raise_406(instance):
    """Abort the current request with a 406 (Not Acceptable) response code.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 406
    """
    instance.response.status = 406
    raise ResponseException(instance.response)


def raise_409(instance):
    """Abort the current request with a 409 (Conflict) response code.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 409
    """
    instance.response.status = 409
    raise ResponseException(instance.response)


def raise_410(instance):
    """Abort the current request with a 410 (Gone) response code.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 410
    """
    instance.response.status = 410
    raise ResponseException(instance.response)


def raise_412(instance, msg=None):
    """Abort the current request with a 412 (Precondition Failed) response
    code. If the message is given it's output as an error message in the
    response body (correctly converted to the requested MIME type).

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 412
    """
    instance.response.status = 412
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)


def raise_415(instance, msg=None):
    """Abort the current request with a 415 (Unsupported Media Type) response
    code. If the message is given it's output as an error message in the
    response body (correctly converted to the requested MIME type).

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 415
    """
    instance.response.status = 415
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)


def raise_500(instance, msg=None):
    """Abort the current request with a 500 (Internal Server Error) response
    code. If the message is given it's output as an error message in the
    response body (correctly converted to the requested MIME type).

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 500
    """
    instance.response.status = 500
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)


def raise_501(instance):
    """Abort the current request with a 501 (Not Implemented) response code.
    Sets the ``Allow`` response header to the return value of the
    :func:`Resource.get_allowed_methods` function.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 501
    """
    instance.response.status = 501
    instance.response.headers['Allow'] = instance.get_allowed_methods()
    raise ResponseException(instance.response)


def raise_503(instance):
    """Abort the current request with a 503 (Service Unavailable) response
    code.

    :param instance: Resource instance (used to access the response)
    :type instance: :class:`webob.resource.Resource`
    :raises: :class:`webob.exceptions.ResponseException` of status 503
    """
    instance.response.status = 503
    raise ResponseException(instance.response)


def _set_location(instance, location):
    """Sets a ``Location`` response header. If the location does not start with
    a slash, the path of the current request is prepended.

    :param instance: Resource instance (used to access the request and
                     response)
    :type instance: :class:`webob.resource.Resource`
    """
    location = str(location)
    if not location.startswith('/'):
        location = urljoin(instance.request_path.rstrip('/') + '/', location)
    instance.response.location = location

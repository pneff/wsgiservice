"""Helper methods to raise responses for the various HTTP status codes."""

class ResponseException(Exception):
    """Wraps a weob.Response object to be thrown as an exception."""
    def __init__(self, response):
        self.response = response

def raise_304(instance):
    instance.response.status = 304
    raise ResponseException(instance.response)

def raise_400(instance, msg=None):
    instance.response.status = 400
    if msg:
        instance.response.body_raw = {'error': msg}
    raise ResponseException(instance.response)

def raise_404(instance):
    instance.response.status = 404
    raise ResponseException(instance.response)

def raise_405(instance):
    instance.response.status = 405
    instance.response.headers['Allow'] = instance.get_allowed_methods()
    raise ResponseException(instance.response)

def raise_412(instance):
    instance.response.status = 412
    raise ResponseException(instance.response)

def raise_501(instance):
    instance.response.status = 501
    instance.response.headers['Allow'] = instance.get_allowed_methods()
    raise ResponseException(instance.response)

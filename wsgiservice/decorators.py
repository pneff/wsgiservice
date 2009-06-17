import time
from wsgiref.handlers import format_date_time
from wsgiservice.objects import MiniResponse
from decorator import decorator

def mount(path):
    """Decorator. Apply on a :class:`wsgiservice.Resource` to mount it at the
    given path. The same can be achived by setting the ``_path`` attribute on
    the class directly.

    :param path: A path to mount this resource on. See
                 :class:`wsgiservice.routing.Router` for a description of how
                 this path has to be formatted.
    """
    def wrap(cls):
        cls._path = path
        return cls
    return wrap


def validate(name, re=None, doc=None):
    """Decorator. Apply on a :class:`wsgiservice.Resource` or any of it's
    methods to validates a parameter on input. When a parameter does not
    validate, a :class:`wsgiservice.exceptions.ValidationException` exception
    will be thrown.
    
    :param name: Name of the input parameter to validate.
    :type name: string
    :param re: Regular expression to search for in the input parameter. If
               this is not set, just validates if the parameter has been set.
    :type re: regular expression
    :param doc: Parameter description for the API documentation.
    :type doc: string
    """
    def wrap(cls_or_func):
        if not hasattr(cls_or_func, '_validations'):
            cls_or_func._validations = {}
        cls_or_func._validations[name] = {'re':re, 'doc':doc}
        return cls_or_func
    return wrap

def expires(duration, currtime=time.gmtime):
    """Decorator. Apply on a :class:`wsgiservice.Resource` method to set the
    max-age cache control parameter to the given duration. Also calculates
    the correct ``Expires`` response header.
    
    :param duration: Age which this resource may have before becoming stale.
    :type duration: :mod:`datetime.timedelta`
    :param currtime: Function used to find out the current UTC time. This is
                     used for testing and not required in production code.
    :type currtime: Function returning a :mod:`time.struct_time`
    """
    @decorator
    def _expires(func, *args, **kwargs):
        "Sets the expirations header to the given duration."
        res = func(*args, **kwargs)
        if not isinstance(res, MiniResponse):
            res = MiniResponse(res)
        res.headers['Cache-Control'] = 'max-age=' + str(duration)
        expires = format_date_time(time.mktime(currtime()) + duration)
        res.headers['Expires'] = str(expires)
        return res
    return _expires

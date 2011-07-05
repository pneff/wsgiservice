import time
from decorator import decorator
from datetime import timedelta
from webob import timedelta_to_seconds


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


def validate(name, re=None, convert=None, doc=None):
    """Decorator. Apply on a :class:`wsgiservice.Resource` or any of it's
    methods to validates a parameter on input. When a parameter does not
    validate, a :class:`wsgiservice.exceptions.ValidationException` exception
    will be thrown.

    :param name: Name of the input parameter to validate.
    :type name: string
    :param re: Regular expression to search for in the input parameter. If
               this is not set, just validates if the parameter has been set.
    :type re: regular expression
    :param convert: Callable to convert the validated parameter value to the
                    final data type. Ideal candidates for this are the
                    built-ins int or float functions. If the function raises a
                    ValueError, this is reported to the client as a 400 error.
    :type convert: callable
    :param doc: Parameter description for the API documentation.
    :type doc: string
    """

    def wrap(cls_or_func):
        if not hasattr(cls_or_func, '_validations'):
            cls_or_func._validations = {}
        cls_or_func._validations[name] = {'re': re, 'convert': convert, 'doc': doc}
        return cls_or_func
    return wrap


def expires(duration, vary=None, currtime=time.time):
    """Decorator. Apply on a :class:`wsgiservice.Resource` method to set the
    max-age cache control parameter to the given duration. Also calculates
    the correct ``Expires`` response header.

    :param duration: Age which this resource may have before becoming stale.
    :type duration: :mod:`datetime.timedelta`
    :param vary: List of headers that should be added to the Vary response
                 header.
    :type vary: list of strings
    :param currtime: Function used to find out the current UTC time. This is
                     used for testing and not required in production code.
    :type currtime: Function returning a :mod:`time.struct_time`
    """
    if isinstance(duration, timedelta):
        duration = timedelta_to_seconds(duration)

    @decorator
    def _expires(func, *args, **kwargs):
        "Sets the expirations header to the given duration."
        res = args[0].response

        res.cache_control.max_age = duration
        res.expires = currtime() + duration

        if vary:
            if res.vary is None:
                res.vary = vary
            else:
                # A bit completed because res.vary is usually a tuple.
                res.vary = list(set(list(res.vary) + list(vary)))

        return func(*args, **kwargs)
    return _expires

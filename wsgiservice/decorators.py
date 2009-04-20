import functools
import time
from wsgiref.handlers import format_date_time
from wsgiservice.objects import MiniResponse

def mount(path):
    "Mounts a Resource at the given path."
    def wrap(cls):
        cls._path = path
        return cls
    return wrap


def validate(name, re=None, doc=None):
    "Validates the given input parameter on input."
    def wrap(cls_or_func):
        if not hasattr(cls_or_func, '_validations'):
            cls_or_func._validations = {}
        cls_or_func._validations[name] = {'re':re, 'doc':doc}
        return cls_or_func
    return wrap


import sys
def expires(duration, currtime=time.gmtime):
    "Sets the expirations header to the given duration."
    def wrap(func):
        if hasattr(func, '_names'):
            names = getattr(func, '_names')
        else:
            names = func.func_code.co_varnames[:func.func_code.co_argcount]
        @functools.wraps(func)
        def decorated(*args, **kwargs):
            res = func(*args, **kwargs)
            if not isinstance(res, MiniResponse):
                res = MiniResponse(res)
            res.headers['Cache-Control'] = 'max-age=' + str(duration)
            expires = format_date_time(time.mktime(currtime()) + duration)
            res.headers['Expires'] = str(expires)
            return res
        decorated._names = names
        return decorated
    return wrap

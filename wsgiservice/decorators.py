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


def expires(duration):
    "Sets the expirations header to the given duration."
    def wrap(func):
        return func
    return wrap

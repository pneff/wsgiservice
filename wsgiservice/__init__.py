"""WsgiService module containing all the root level definitions."""

def mount(path):
    "Mounts a Resource at the given path."
    def decorator(f):
        pass
    return decorator

def get_app(defs):
    """Returns a WSGI app which serves the objects in the defs. Usually this
    is called with return value globals() from the module where the resources
    are defined. The returned WSGI application will serve all subclasses of
    Resource.
    """



class Resource(object):
    """Base class for all WsgiService resources. A resourse is a unique REST
    endpoint which accepts different methods for different actions."""


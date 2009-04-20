"""WsgiService module containing all the root level definitions."""
import wsgiservice.routing
from wsgiservice.decorators import mount, validate, expires
from wsgiservice.objects import Request, Response
from wsgiservice.application import get_app

class duration(object):
    def __getattr__(self, key):
        print "duration: {0}".format(key)
        return key
duration = duration()

class Resource(object):
    """Base class for all WsgiService resources. A resourse is a unique REST
    endpoint which accepts different methods for different actions."""

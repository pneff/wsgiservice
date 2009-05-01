"""This root level directives are importend from the submodules. They are
made available here as well to keep the number of imports to a minimum for
most applications.
"""
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

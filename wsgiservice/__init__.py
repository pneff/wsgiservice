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
    endpoint which accepts different methods for different actions.
    
    For each HTTP call the corresponding method (equal to the HTTP method)
    will be called. Additionally there are a few special methods used while
    serving resources:
    
    * ``get_etag``: Returns a string to be used as the ETag for this resource.
      Used to set the ``ETag`` response headers and for conditional requests
      using the ``If-Match`` and ``If-None-Match`` request headers.
    * ``get_last_modified``: Return a :class:`datetime.datetime` object of the
      when the resource was last modified. Used to set the ``Last-Modified``
      response header and for conditional requests using the
      ``If-Modified-Since`` and ``If-Unmodified-Since`` request headers.
    """

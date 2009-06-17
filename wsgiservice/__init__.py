"""This root level directives are importend from the submodules. They are
made available here as well to keep the number of imports to a minimum for
most applications.
"""
import wsgiservice.routing
from wsgiservice.decorators import mount, validate, expires
from wsgiservice.objects import Response
from wsgiservice.application import get_app
from wsgiservice.resource import Resource
from wsgiservice.status import *

class duration(object):
    def __getattr__(self, key):
        print "duration: {0}".format(key)
        return key
duration = duration()

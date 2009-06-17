class Resource(object):
    """Base class for all WsgiService resources. A resourse is a unique REST
    endpoint which accepts different methods for different actions.
    
    For each HTTP call the corresponding method (equal to the HTTP method)
    will be called.
    """
    def get_etag(self):
        """Returns a string to be used as the ETag for this resource. Used to
        set the ``ETag`` response headers and for conditional requests using
        the ``If-Match`` and ``If-None-Match`` request headers.
        """
        return None

    def get_last_modified(self):
        """Return a :class:`datetime.datetime` object of the when the resource
        was last modified. Used to set the ``Last-Modified`` response header
        and for conditional requests using the ``If-Modified-Since`` and
        ``If-Unmodified-Since`` request headers.

        :rtype: :class:`datetime.datetime`
        """
        return None

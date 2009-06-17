"""Implements a simple routing class."""
import re
import wsgiservice

class Router(object):
    """Simple routing. Path parameters can be extracted with the syntax
    {keyword} where keyword is the path parameter. That parameter will then
    be passed on to the called request method.

    :param resources: A list of :class:`wsgiservice.Resource` classes to be
                      routed to.
    """
    def __init__(self, resources):
        self._routes = []
        search_vars = re.compile(r'\{(\w+)\}').finditer
        for resource in resources:
            # Compile regular expression for each path
            path, regexp, prev_pos = resource._path, '^', 0
            for match in search_vars(path):
                regexp += re.escape(path[prev_pos:match.start()])
                # .+? - match any character but non-greedy
                regexp += '(?P<{0}>.+?)'.format(match.group(1))
                prev_pos = match.end()
            regexp += re.escape(path[prev_pos:])
            # Allow an extension to overwrite the mime type
            extensions = "|".join(wsgiservice.Response._extension_map.keys())
            regexp += '(?P<_extension>' + extensions + ')?$'
            self._routes.append((re.compile(regexp).match, resource))

    def __call__(self, path):
        for match, resource in self._routes:
            retval = match(path)
            if retval:
                return (retval.groupdict(), resource)

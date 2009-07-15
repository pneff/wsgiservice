"""Implements a simple routing class."""
import re
import wsgiservice


class Router(object):
    """Simple routing. Path parameters can be extracted with the syntax
    ``{keyword}`` where keyword is the path parameter. That parameter will
    then be passed on to the called request method.

    :param resources: A list of :class:`wsgiservice.Resource` classes to be
                      routed to.
    """

    def __init__(self, resources):
        """Constructor. Extracts all the paths from the given resources.

        :param resources: List of :class:`wsgiservice.resource.Resource`
                          classes to be served by this application.
        """
        resources = self._get_sorted(resources)
        self._routes = self._compile(resources)

    def _get_sorted(self, resources):
        """Order the resources by priority - the most specific paths come
        first.

        :param resources: List of :class:`wsgiservice.resource.Resource`
                          classes to be served by this application.
        """
        tmp = []
        for resource in resources:
            path = resource._path
            # Each slash counts as 10 priority, each variable takes one away
            priority = path.count('/') * 10 - path.count('{')
            tmp.append((priority, resource))
        return [resource for prio, resource in reversed(sorted(tmp))]

    def _compile(self, resources):
        """Compiles a list of match functions (using regular expressions) for
        the paths. Returns a list of two-item tuples consisting of the match
        function and the resource class. The list is in the same order as the
        resources parameter.

        :param resources: List of :class:`wsgiservice.resource.Resource`
                          classes to be served by this application.
        """
        routes = []
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
            extensions = "|".join([ext for ext, _ in resource.EXTENSION_MAP])
            regexp += '(?P<_extension>' + extensions + ')?$'
            routes.append((re.compile(regexp).match, resource))
        return routes

    def __call__(self, path):
        """Return the resource which best matches the given path. Returns a
        two-item tuple of extracted path parameters (as dict) and the resource
        class if a match is found. Otherwise returns None.

        :param path: The path requested by the client.
        :type path: str
        """
        for match, resource in self._routes:
            retval = match(path)
            if retval:
                return (retval.groupdict(), resource)

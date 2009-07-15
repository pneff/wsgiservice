"""Declares different exceptions as used throughout WsgiService."""
import logging

logger = logging.getLogger(__name__)


class ValidationException(Exception):
    """Exception thrown when a validation fails. See
    :func:`wsgiservice.decorators.validate` for it's use.
    """

    def __init__(self, *args, **kwargs):
        logger.error("ValidationException: %s", args[0])
        Exception.__init__(self, *args, **kwargs)


class ResponseException(Exception):
    """Wraps a :class:`webob.Response` object to be thrown as an exception."""

    def __init__(self, response):
        """Constructor.

        :param response: The response to wrap.
        :type response: :class:`webob.Response`
        """
        self.response = response

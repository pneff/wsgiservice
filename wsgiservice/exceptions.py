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

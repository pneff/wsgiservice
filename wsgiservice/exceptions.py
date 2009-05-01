"""Declares different exceptions as used through WsgiService."""
import logging

logger = logging.getLogger(__name__)

class ValidationException(Exception):
    def __init__(self, *args, **kwargs):
        logger.error("ValidationException: %s", args[0])
        Exception.__init__(self, *args, **kwargs)

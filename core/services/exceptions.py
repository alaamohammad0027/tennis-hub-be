import logging

from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class CustomAPIException(APIException):
    """
    Custom API exception class to handle custom error messages.
    """

    status_code = 400
    default_detail = "An error occurred."
    default_code = "ERROR"

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        self.detail = {
            "error": {
                "code": code,
                "message": detail,
                "details": detail,
                "status": self.status_code,
            }
        }


def custom_exception_handler(exc, context):
    """
    Custom exception handler to handle custom error messages.
    """
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            custom_response_data = {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Validation failed.",
                    "details": response.data,
                    "status": response.status_code,
                }
            }
        elif isinstance(exc, CustomAPIException):
            custom_response_data = exc.detail
        elif isinstance(exc, APIException):
            custom_response_data = {
                "error": {
                    "code": "API_ERROR",
                    "message": "An API error occurred.",
                    "details": response.data,
                    "status": response.status_code,
                }
            }
        else:
            custom_response_data = {
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "An internal server error occurred.",
                    "details": str(exc),
                    "status": 500,
                }
            }
            # Log the error for debugging purposes
            logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

        response.data = custom_response_data

    return response

"""Tests for registered HTTP error handlers."""

import unittest

from service.common import error_handlers, status
from service.models import DataValidationError
from wsgi import app


class TestErrorHandlers(unittest.TestCase):
    """HTTP error handler tests."""

    def setUp(self):
        self.context = app.test_request_context("/")
        self.context.push()

    def tearDown(self):
        self.context.pop()

    def test_validation_error_uses_bad_request_handler(self):
        """It should convert data validation errors into a bad request response"""
        response, code = error_handlers.request_validation_error(
            DataValidationError("invalid data")
        )

        self.assertEqual(code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.get_json()["message"], "invalid data")

    def test_http_error_handlers(self):
        """It should return the expected response for each supported HTTP error"""
        handlers = (
            (error_handlers.bad_request, status.HTTP_400_BAD_REQUEST, "Bad Request"),
            (error_handlers.not_found, status.HTTP_404_NOT_FOUND, "Not Found"),
            (
                error_handlers.method_not_supported,
                status.HTTP_405_METHOD_NOT_ALLOWED,
                "Method not Allowed",
            ),
            (
                error_handlers.mediatype_not_supported,
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                "Unsupported media type",
            ),
            (
                error_handlers.internal_server_error,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Internal Server Error",
            ),
        )

        for handler, code, error in handlers:
            with self.subTest(code=code):
                response, response_code = handler(RuntimeError("failure"))

                self.assertEqual(response_code, code)
                self.assertEqual(response.get_json()["error"], error)

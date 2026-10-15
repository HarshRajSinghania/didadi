import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from src.matrix_http import MatrixError, request


class MatrixHTTPTests(unittest.TestCase):
    def test_error_response_preserves_status_and_valid_matrix_body(self):
        for raw, expected in [(b'', {}), (b'<html>unavailable</html>', {}),
                              (b'[]', {}), (b'null', {}), (b'"error"', {}),
                              (b'\xff', {}),
                              (b'{"errcode":"M_UNAVAILABLE"}', {'errcode': 'M_UNAVAILABLE'})]:
            with self.subTest(raw=raw):
                error = HTTPError('http://localhost', 503, 'unavailable', {}, io.BytesIO(raw))
                with patch('src.matrix_http.urlopen', side_effect=error):
                    with self.assertRaises(MatrixError) as caught:
                        request('http://localhost', 'GET', '/test')
                self.assertEqual(caught.exception.status, 503)
                self.assertEqual(caught.exception.body, expected)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from metascrape import utils

import mock
import unittest


class UtilsTestCase(unittest.TestCase):

    def test_extract_headers(self):
        mock_response = mock.Mock()

        mock_response.headers = {
            "Accept-Ranges": "none",
            "Connection": "close",
            "Content-Length": "230",
            "Content-Type": "text/plain",
            "Date": "Mon, 15 Jul 2019 19:43:30 GMT",
            "Etag": "abcdefg",
            "Last-Modified": "Thu, 11 Jul 2019 23:18:47 GMT",
            "Server": "EC2ws",
        }

        result = utils.extract_headers(mock_response)

        self.assertNotIn('Content-Length', result.keys())
        self.assertNotIn('Date', result.keys())
        self.assertNotIn('Etag', result.keys())
        self.assertNotIn('Last-Modified', result.keys())

        self.assertIn('Server', result.keys())

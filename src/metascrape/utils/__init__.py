#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

import logging
import tzlocal


class LoggingFormatter(logging.Formatter):
    """A custom logging formatter which supports more date formatting options."""

    DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

    TIMEZONE = tzlocal.get_localzone()

    converter = datetime.utcfromtimestamp

    def formatTime(self, record, datefmt=None):
        """Format time using our custom time formatter."""
        if not datefmt:
            datefmt = LoggingFormatter.DEFAULT_DATE_FORMAT

        # by default, no timezone is associated with a datetime, so we create a new one with a timezone
        record_time = LoggingFormatter.TIMEZONE.localize(self.converter(record.created))

        return "".join([
            # iso-8601 slug prefix
            record_time.strftime("%Y-%m-%dT%H:%M:%S"),
            # microsecond to millisecond conversion
            ".{:03.0f}".format(record.msecs),
            # iso-8601 timezone postfix
            record_time.strftime("%z"),
        ])


def extract_headers(response):
    """Extract relevant headers from a response into a dictionary."""
    result = {}

    for key in response.headers.keys():
        if isinstance(key, bytes):
            key = key.decode('utf-8')

        value = response.headers.get(key)

        if isinstance(value, bytes):
            value = value.decode('utf-8')

        if key in ('Date', 'Content-Length', 'Etag','Last-Modified'):
            continue

        result[key] = value

    return result

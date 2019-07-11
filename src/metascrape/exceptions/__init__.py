#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class WrongServiceException(Exception):
    """
    An exception thrown when attempting to crawl the wrong metadata service.

    If, say, the EC2 crawler attempts to crawl the GCP metadata service, this exception will be raised.
    """

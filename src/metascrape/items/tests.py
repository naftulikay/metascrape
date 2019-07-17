#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from metascrape.items import Matchers, Route

import unittest


class MatcherTestCase(unittest.TestCase):
    """Regular expression test case for EC2 route objects."""

    def test_aws_account_id(self):
        """Test AWS account ID matching."""
        for account in ['012345678901', '109876543210']:
            self.assertIsNotNone(Matchers.AWS_ACCOUNT_ID.search(account))

        for account in ['123456', '012345678901234567890a']:
            self.assertIsNone(Matchers.AWS_ACCOUNT_ID.search(account))

    def test_aws_identifier(self):
        """Test AWS identifier matching."""
        for id in ["ami-0123456789abdef01", "eni-0123456789abdef01", "i-0123456789abdef01", "r-0123456789abdef01", \
                "sg-0123456789abdef01", "subnet-0123456789abdef01", "vpc-01234567"]:
            self.assertIsNotNone(Matchers.AWS_IDENTIFIER.search(id))

        for id in ["i-1234", "I-01234567"]:
            self.assertIsNone(Matchers.AWS_IDENTIFIER.search(id))

    def test_ec2_hostname_prefix(self):
        """Test EC2 hostname prefix matching."""
        public = "ec2-1-1-1-1.us-west-2.compute.amazonaws.com"
        private = "ip-10-0-0-1.us-west-2.compute.internal"

        # test public
        self.assertIsNotNone(Matchers.EC2_HOSTNAME_PREFIX.search(public))

        match = Matchers.EC2_HOSTNAME_PREFIX.search(public)

        self.assertEqual("ec2", match.group('type'))
        self.assertEqual("1", match.group('octet_0'))
        self.assertEqual("1", match.group('octet_1'))
        self.assertEqual("1", match.group('octet_2'))
        self.assertEqual("1", match.group('octet_3'))

        # test private
        self.assertIsNotNone(Matchers.EC2_HOSTNAME_PREFIX.search(private))

        match = Matchers.EC2_HOSTNAME_PREFIX.search(private)

        self.assertEqual("ip", match.group('type'))
        self.assertEqual("10", match.group('octet_0'))
        self.assertEqual("0", match.group('octet_1'))
        self.assertEqual("0", match.group('octet_2'))
        self.assertEqual("1", match.group('octet_3'))

    def test_ipv4_address(self):
        """Test IPv4 address matching."""
        for addr in ["0.0.0.0", "255.255.255.255", "127.0.0.1", "10.0.0.1"]:
            self.assertIsNotNone(Matchers.IPV4_ADDRESS.search(addr))

        for addr in ['bc', '10.0.0', '10.10.10.']:
            self.assertIsNone(Matchers.IPV4_ADDRESS.search(addr))

    def test_mac_address(self):
        """Test MAC address matching."""
        for mac in ['00:00:00:00:00:00', 'af:10:23:70:ba:cd']:
            self.assertIsNotNone(Matchers.MAC_ADDRESS.search(mac))

        for mac in ['ze:do:gi:is:de:ad']:
            self.assertIsNone(Matchers.MAC_ADDRESS.search(mac))


class RouteTestCase(unittest.TestCase):
    """Tests cases against the Route item."""

    def test_path_postfix(self):
        """Tests getting the path postfix from a route."""
        self.assertEqual("meta-data/local-hostname", Route(path="/latest/meta-data/local-hostname").path_postfix)
        self.assertEqual("meta-data/public-keys/", Route(path="/latest/meta-data/public-keys/").path_postfix)

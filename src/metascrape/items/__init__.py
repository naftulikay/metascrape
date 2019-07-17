#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ipaddress import IPv4Address

import json
import re
import scrapy
import string


class Matchers(object):

    AWS_ACCOUNT_ID = re.compile(r'\b(?P<account_id>\d{12})\b')

    AWS_IDENTIFIER = re.compile(r'\b(?P<aws_id>(?P<type>[a-z]{1,6})-(?P<id>[0-9a-f]{8,32}))\b')

    EC2_HOSTNAME_PREFIX = re.compile(r'\b(?P<type>ec2|ip)-(?P<octet_0>\d{1,3})-(?P<octet_1>\d{1,3})-(?P<octet_2>\d{1,3})-(?P<octet_3>\d{1,3})\.(?P<region>[^.]+)\.compute\.(?P<root_domain>amazonaws\.com|internal)\b')

    IPV4_ADDRESS = re.compile(r'\b(?P<ipv4_address>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', re.I)

    MAC_ADDRESS = re.compile(r'\b(?P<mac_address>[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})\b')


class Route(scrapy.Item):
    """An item representing an available route for the service."""

    """The path of the given route."""
    path = scrapy.Field()

    """The headers returned by the given route."""
    headers = scrapy.Field()

    """The raw response."""
    response = scrapy.Field()

    """The response encoding, either 'text' or 'base64'."""
    response_encoding = scrapy.Field()

    @property
    def path_postfix(self):
        """Return the path postfix without the API version prepended."""
        path = self["path"]
        path_components = list(filter(lambda pc: len(pc) > 0, path.split("/")))

        return "{}{}".format("/".join(path_components[1:]), "/" if path.endswith("/") else "")

    def sanitize(self):
        """Sanitize this route's data to redact private information."""
        self._sanitize_ip_addresses()
        self._sanitize_mac_addresses()
        self._sanitize_account_ids()
        self._sanitize_host_name()
        self._sanitize_aws_identifiers()
        self._sanitize_iam_credentials()
        self._sanitize_instance_identity()

    def _sanitize_ip_addresses(self):
        """Sanitize public and private IP addresses in this route."""
        path, response = self["path"], self["response"]

        def ip_replace(match):
            addr = IPv4Address(match.group('ipv4_address'))
            octets = list(map(lambda o: int(o), str(addr).split('.')))

            if addr.is_private:
                return "10.0.0.{}".format(0 if octets[-1] == 0 else 1)
            elif addr.is_global:
                return "1.1.1.{}".format(0 if octets[-1] == 0 else 1)
            else:
                return str(addr)

        self["path"], self["response"] = Matchers.IPV4_ADDRESS.sub(ip_replace, path), \
                Matchers.IPV4_ADDRESS.sub(ip_replace, response)

    def _sanitize_mac_addresses(self):
        """Sanitize MAC addresses in this route."""
        path, response = self["path"], self["response"]

        def mac_replace(match):
            return "01:23:45:67:89:ab"

        self["path"], self["response"] = Matchers.MAC_ADDRESS.sub(mac_replace, path), \
                Matchers.MAC_ADDRESS.sub(mac_replace, response)

    def _sanitize_host_name(self):
        """Sanitize the host name, which reflects the actual IP."""
        path, response = self["path"], self["response"]

        if path.split("/")[-1] not in ["hostname", "local-hostname", "public-hostname"]:
            return

        match = Matchers.EC2_HOSTNAME_PREFIX.search(response)

        if not match:
            raise Exception("Unable to sanitize hostname: {}".format(response))

        host_type = match.group('type')
        octet_0, octet_1, octet_2, octet_3 = match.group('octet_0'), match.group('octet_1'), match.group('octet_2'), \
                match.group('octet_3')

        postfix = ".".join(response.split('.')[1:])

        if host_type == "ec2":
            # public host
            octet_0, octet_1, octet_2, octet_3 = "1", "1", "1", "1"
        else:
            # private host
            octet_0, octet_1, octet_2, octet_3 = "10", "0", "0", "1"

        self["response"] = "{}-{}-{}-{}-{}.{}".format(host_type, octet_0, octet_1, octet_2, octet_3, postfix)


    def _sanitize_account_ids(self):
        """Sanitize AWS account IDs in this route."""
        path, response = self["path"], self["response"]

        def account_replace(match):
            return "012345678901"

        self["path"], self["response"] = Matchers.AWS_ACCOUNT_ID.sub(account_replace, path), \
                Matchers.AWS_ACCOUNT_ID.sub(account_replace, response)

    def _sanitize_aws_identifiers(self):
        """Sanitize identifiers for AWS objects such as EC2 instance ids."""
        replacer = "0123456789abcdef"

        path, response = self["path"], self["response"]

        def aws_id_replace(match):
            resource_type, resource_id = match.group('type'), match.group('id')

            return "{}-{}".format(resource_type, "".join(
                [replacer[i % len(replacer)] for i in range(len(resource_id))]
            ))

        self["path"], self["response"] = Matchers.AWS_IDENTIFIER.sub(aws_id_replace, path), \
                Matchers.AWS_IDENTIFIER.sub(aws_id_replace, response)

    def _sanitize_iam_credentials(self):
        """Sanitize sensitive IAM credentials."""
        path, response = self["path"], self["response"]

        if not path.endswith("/meta-data/identity-credentials/ec2/security-credentials/ec2-instance"):
           return

        # okay so now we've reached our IAM credentials.
        response = json.loads(response)

        response["AccessKeyId"] = "A" * 20
        response["SecretAccessKey"] = "B" * 40
        response["Token"] = "C" * 676

        self["response"] = json.dumps(response, indent=4)

    def _sanitize_instance_identity(self):
        """Sanitize instance identity cryptographic data."""
        # the format of these items is complicated, see issue #2
        path, response = self["path"], self["response"]

        if path.endswith("/dynamic/instance-identity/pkcs7"):
            response = "A" * 828

        if path.endswith("/dynamic/instance-identity/rsa2048"):
            response = "B" * 1063

        if path.endswith("/dynamic/instance-identity/signature"):
            response = "C" * 128

        self["path"], self["response"] = path, response

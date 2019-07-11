#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from metascrape.exceptions import WrongServiceException
from metascrape.items import Route
from metascrape import utils

import base64

import scrapy


class EC2Spider(scrapy.spiders.Spider):
    """
    A spider for crawling the EC2 metadata service.

    The EC2 metadata service has a few weird gotchas to understand how to crawl it.

     - The EC2 metadata service will return a header `Server: EC2ws` which can be used to identify it.
     - The first-level keys contain the different available versions of the service. `latest` is generally what you
       want. These never end in a slash, yet are directories.
     - The second-level keys presently contain at max three keys: `dynamic`, `meta-data`, and `user-data` and none of
       these end in a slash.
     - Anything at third-level and below will contain a trailing slash if the entry is a directory, and won't if it is
       just a directory entry.
     - Most things are text/plain content encoding, with `{version}/user-data` always being application/octet-stream.
     - Some entries are JSON, yet are text/plain, c.f. `{version}/meta-data/identity-credentials/ec2/info`.
     - Some entries are weird arrays, c.f. `{version}/meta-data/public-keys/`, which returns values formatted as
       `{index}={key_name}`. To traverse this array-like entry, the following path should be used:
       `{version}/meta-data/public-keys/{index}`, which will yield the key name. Next, the key fingerprint can be
       fetched at `{version}/meta-data/public-keys/{index}/{key_name}. This appears to be the only use of this array
       format.

    To keep things stupid and simple, our data model will be a JSON dictionary where each key is a key and each value
    is either a string/byte-array or another dictionary.
    """

    name = "metascraper.spiders.EC2Spider"

    def __init__(self, metadata_host, metadata_port):
        """Construct a new spider with the given metadata host and port."""
        self.metadata_host, self.metadata_port = metadata_host, metadata_port

    def get_url(self, path=None):
        """Get the request URL for a given path."""
        return "http://{}:{}/{}".format(self.metadata_host, self.metadata_port, path if path is not None else "")

    def create_route(self, response, path=None):
        """Given a response, create a route object item."""
        if path is None or len(path) == 0:
            path = "/"

        if not path.startswith("/"):
            path = "/" + path

        if response.headers.get('Content-Type', b"text/plain").decode("utf-8") == "application/octet-stream":
            body, body_type = base64.encodebytes(response.body).strip().decode('utf-8'), "base64"
        else:
            body, body_type = response.text, "text"

        return Route(path=path, headers=utils.extract_headers(response), response=body,
            response_encoding=body_type)

    def start_requests(self):
        """Start scraping the given urls."""
        self.logger.debug("Starting to scrape the EC2 metadata service at %s:%d",
            self.metadata_host, self.metadata_port)

        return [scrapy.Request(self.get_url(), callback=self.parse_apex)]

    def parse_apex(self, response):
        """
        Parse the root URL of the metadata service, yielding each available EC2 metadata service API version.
        """
        self.logger.debug("Received index response: %d", response.status)

        if response.headers.get('Server', None) != b'EC2ws':
            raise WrongServiceException("Expected EC2 metadata service, instead got Server: {}".format(
                response.headers.get('Server', '(empty)')))

        self.logger.debug("Successfully identified endpoint as EC2 metadata service.")

        yield self.create_route(response, "/")

        for api_version in response.text.splitlines():
            # each of these is a directory
            self.logger.debug("Discovered API version %s", api_version)

            yield scrapy.Request(self.get_url(api_version), callback=self.parse_api_data_types,
                meta={ "path": api_version, "api_version": api_version })

    def parse_api_data_types(self, response):
        """
        Parse the available data types for a given API version.

        These are going to be `dynamic`, `meta-data`, and `user-data`, each with its own set of rules.
        """
        path, api_version = response.meta.get('path'), response.meta.get('api_version')

        self.logger.debug("Discovered data types for API version %s", api_version)

        yield self.create_route(response, path)

        for data_type in response.text.splitlines():
            self.logger.debug("Discovered %s/%s data type.", api_version, data_type)

            next_path = "/".join([path, data_type])

            if data_type == "user-data":
                # user-data is a byte-array and non traversable
                yield scrapy.Request(self.get_url(next_path), callback=self.parse_user_data,
                    meta={ 'path': next_path, 'api_version': api_version })
            else:
                # everything else (`dynamic` and `meta-data`) should be parsed as a directory structure
                yield scrapy.Request(self.get_url(next_path), callback=self.parse_directory,
                    meta={ 'path': next_path + '/', 'api_version': api_version })

    def parse_user_data(self, response):
        """
        Parse user data for the given API version.

        This will be `application/octet-stream`, a byte array, though it's typically strings.
        """
        path, api_version = response.meta.get('path'), response.meta.get('api_version')

        self.logger.debug("Discovered user-data for API version %s", api_version)

        yield self.create_route(response, path)

    def parse_directory(self, response):
        """Parse a directory structure."""
        path, api_version = response.meta.get('path'), response.meta.get('api_version')

        self.logger.debug("Crawling directory %s", path)

        yield self.create_route(response, path)

        for entry in response.text.splitlines():
            next_path = (path + entry) if path.endswith('/') else "/".join([path, entry])

            if entry.endswith('/'):
                self.logger.debug("Found a directory: %s", next_path)

                if next_path.endswith('/meta-data/public-keys/'):
                    # deal with odd public key case
                    yield scrapy.Request(self.get_url(next_path), callback=self.parse_public_key_dir,
                        meta={ 'path': next_path, 'api_version': api_version })
                else:
                    yield scrapy.Request(self.get_url(next_path), callback=self.parse_directory,
                        meta={ 'path': next_path, 'api_version': api_version })
            else:
                self.logger.debug("Found a 'file': %s", next_path)
                yield scrapy.Request(self.get_url(next_path), callback=self.parse_file,
                    meta={ 'path': next_path, 'api_version': api_version })

    def parse_public_key_dir(self, response):
        """Parse the SSH key metadata."""
        path, api_version = response.meta.get('path'), response.meta.get('api_version')

        yield self.create_route(response, path)

        for entry in response.text.splitlines():
            # each entry is of format {index:02d}={key_name}
            index = entry.split('=')[0]

            # the next path to crawl is {current_path}/{index}/ - note trailing slash
            next_path = ((path + index) if path.endswith('/') else "/".join([path, index])) + "/"

            yield scrapy.Request(self.get_url(next_path), callback=self.parse_directory,
                meta={ 'path': next_path, 'api_version': api_version })

    def parse_file(self, response):
        """Parse a 'file' as listed from a 'directory."""
        path, api_version = response.meta.get('path'), response.meta.get('api_version')

        self.logger.debug("Parsed Entry: %s: %s", path, str(response.body))

        yield self.create_route(response, path)

    def parse(self, response):
        """Default callback for processing responses without defined callbacks."""
        # raise an exception because everything should be explicit
        raise Exception("NO CALLBACK")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from metascrape import items

import json
import logging


class JSONItemPipeline(object):
    """"""

    @classmethod
    def from_crawler(cls, crawler):
        """Construct a new pipeline from the given crawler."""
        return cls(output_file=crawler.settings.get("JSON_OUTPUT_FILE"))

    def __init__(self, output_file):
        """Construct a new JSON item pipeline."""
        self.result = { "routes": {} }
        self.logger = logging.getLogger("metascrape.pipelines.{}".format(self.__class__.__name__))
        self.output_file = output_file

    def open_spider(self, spider):
        """Callback method called when a spider has been opened."""
        self.logger.debug("Spider %s has been opened.", spider)

    def process_item(self, item, spider):
        """Process an item received from the spider."""
        self.logger.debug("Received an item from the %s spider: %s", spider, item)

        if isinstance(item, items.Route):
            # sanitize the item
            item.sanitize()

            # extract values
            path, headers, response, response_encoding = item["path"], item["headers"], item["response"], \
                item["response_encoding"]

            # insert into output
            self.result.get('routes')[path] = {
                'path': path,
                'headers': headers,
                'response': response,
                'response_encoding': response_encoding,
            }

    def close_spider(self, spider):
        """Callback method called when a spider is closed."""
        self.logger.debug("Spider %s has been closed.", spider)

        with open(self.output_file, 'w') as f:
            f.write(json.dumps(self.result, sort_keys=True, indent=2))

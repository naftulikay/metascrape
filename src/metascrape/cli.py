#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from metascrape.spiders import EC2Spider
from metascrape.utils import LoggingFormatter

from scrapy.crawler import CrawlerProcess

import argparse
import logging
import scrapy


def main():
    parser = argparse.ArgumentParser(
        prog='metascrape',
        description="A scraper in Python/Scrapy for extracting cloud provider instance metadata.",
    )

    parser.add_argument('-H', '--host', default='169.254.169.254',
        help="The host where the instance metadata service lives.")
    parser.add_argument('-o', '--output', default="metadata.json",
        help="The output file to store scraped information in.")
    parser.add_argument('-p', '--port', default=80, type=int,
        help="The port where the instance metadata service is listening.")
    parser.add_argument('-v', action='count', dest='verbosity', default=0,
        help="Set logging verbosity. Pass multiple times to increase verbosity.")

    args = parser.parse_args()

    # setup logging
    setup_logging(args.verbosity)

    logger = logging.getLogger("metascrape")
    logger.info("Starting scraper...")

    scrape(args.host, args.port, args.output)


def setup_logging(verbosity):
    """Setup and configure Python logging."""
    logging.addLevelName(logging.WARNING, "WARN")

    console = logging.StreamHandler()
    console.setFormatter(LoggingFormatter(
        fmt="%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
    ))

    logging.getLogger(None).setLevel(logging.WARNING)
    logging.getLogger(None).addHandler(console)

    logging.getLogger('metascrape').setLevel(max(logging.WARNING - (verbosity * 10), 0))


def scrape(host, port, output_file):
    """Execute the scraper on the given host and port."""
    process = CrawlerProcess({
        'BOT_NAME': 'metascrape',
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'ITEM_PIPELINES': {
            'metascrape.pipelines.JSONItemPipeline': 1000
        },
        'JSON_OUTPUT_FILE': output_file,
        'LOG_ENABLED': False,
    })

    process.crawl(EC2Spider, metadata_host=host, metadata_port=port)
    process.start()


if __name__ == "__main__":
    main()

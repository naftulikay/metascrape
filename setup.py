#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name = "metascrape",
    version = "0.0.1",
    packages = find_packages("src"),
    package_dir = { "": "src" },
    install_requires = [
        "setuptools",
        "scrapy",
    ],
    entry_points = {
        "console_scripts": [
            "metascrape = metascrape.cli:main",
        ]
    },
)

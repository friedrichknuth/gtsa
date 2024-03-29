#!/usr/bin/env python

from distutils.core import setup
import setuptools

setup(
    name="gtsa",
    version="0.1",
    description="Functions to compute continuous glacier change from temporally and spatially sparse geodetic measurements",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "download_data=gtsa.cli.download_data:main",
            "create_stack=gtsa.cli.create_stack:main",
            "create_cogs=gtsa.cli.create_cogs:main",
            "create_cog_map=gtsa.cli.create_cog_map:main",
            "gtsa=gtsa.cli.gtsa:main",
        ]
    },
)

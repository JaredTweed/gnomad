#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#   _____ ____  _            _
#  |_   _| __ )| | ___   ___| | __
#    | | |  _ \| |/ _ \ / __| |/ /
#    | | | |_) | | (_) | (__|   <
#    |_| |____/|_|\___/ \___|_|\_\
#
# An anti-capitalist ad-blocker that uses the hosts file
# Copyright (C) 2021-2025 Camelia Lavender <camelia@tblock.me>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Import modules
from tblock import __version__
import os.path
import sys

# Check if setuptools is installed

try:
    from setuptools import setup
except ImportError:
    setup = None
    sys.exit("Error: setuptools is not installed\nTry to run python -m pip install setuptools --upgrade")

# Open README to define long description

with open(os.path.join(os.path.dirname(__file__), "README.md"), "rt") as readme:
    long_description = readme.read()

# Open requirements.txt to define requirements

requirements = []

with open(os.path.join(os.path.dirname(__file__), "requirements.txt"), "rt") as f:
    for requirement in f.readlines():
        if requirement != "\n" and requirement[0:1] != "#":
            requirements.append(requirement.split("\n")[0])


if __name__ == "__main__":
    setup(
            name="tblock",
            version=__version__,
            description="An anti-capitalist ad-blocker that uses the hosts file",
            long_description=long_description,
            long_description_content_type="text/markdown",
            url="https://tblock.codeberg.page/",
            author="Twann",
            author_email="tw4nn@disroot.org",
            license="GPLv3",
            packages=["tblock", "tblock.converter", "tblock.argumentor", "tblock.daemon"],
            install_requires=requirements,
            entry_points={"console_scripts": [
                "tblock = tblock.cli:run",
                "tblockc = tblock.cli:run_converter",
                "tblockd = tblock.cli:run_daemon"
            ]},
            classifiers=[
                "Environment :: Console",
                "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Operating System :: OS Independent",
            ],
    )

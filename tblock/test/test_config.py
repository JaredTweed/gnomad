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

import tblock
import tblock.exceptions
import os
import unittest
from . import _create_env

# Change PATH variables
__root__ = os.path.join(os.path.dirname(__file__), "fake_root")
__prefix__ = os.path.join(__root__, "usr", "lib")
tblock.config.Path.PREFIX = __prefix__
tblock.config.Path.CACHE = os.path.join(__root__, "var", "cache")
tblock.config.Path.CONFIG = os.path.join(__root__, "etc", "tblock.conf")
tblock.config.Path.DAEMON_PID = os.path.join(__root__, "run", "tblock.pid")
tblock.config.Path.RULES_DATABASE = os.path.join(__prefix__, "user.db")
tblock.config.Path.DATABASE = os.path.join(__prefix__, "storage.sqlite")
tblock.config.Path.DB_LOCK = os.path.join(__prefix__, ".db_lock")
tblock.config.Path.HOSTS = os.path.join(__root__, "etc", "hosts")
tblock.config.Path.HOSTS_BACKUP = os.path.join(__prefix__, "hosts.bak")
tblock.config.Path.BUILT_HOSTS_BACKUP = os.path.join(__prefix__, "active.hosts.bak")
tblock.config.Path.LOGS = os.path.join(__root__, "var", "log", "tblock.log")
tblock.config.Path.TMP_DIR = os.path.join(__root__, "tmp", "tblock")


class TestHostsSafeDef(unittest.TestCase):

    def test_hosts_safe(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        self.assertTrue(
            tblock.hosts_are_safe()
        )

    def test_hosts_unsafe(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        with open(tblock.config.Path.HOSTS, "at") as f:
            f.write("#\n")
        self.assertFalse(
            tblock.hosts_are_safe()
        )

    def test_inactive(self):
        _create_env()
        self.assertFalse(
            tblock.hosts_are_safe()
        )


class TestHostsDefaultDef(unittest.TestCase):

    def test_active(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        self.assertFalse(
            tblock.config.hosts_are_default()
        )

    def test_inactive(self):
        _create_env()
        self.assertTrue(
            tblock.config.hosts_are_default()
        )


if __name__ == "__main__":
    unittest.main()

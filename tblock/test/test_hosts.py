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


class TestEnableDef(unittest.TestCase):

    def test_enable_new(self):
        _create_env()
        tblock.enable_protection(quiet=True, do_not_prompt=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertEqual(
            content,
            ""
        )

    def test_enable_active(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.enable_protection(quiet=True, do_not_prompt=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertNotEqual(
            content,
            ""
        )

    def test_enable_inactive(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.restore_hosts(quiet=True, do_not_prompt=True)
        tblock.enable_protection(quiet=True, do_not_prompt=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertNotEqual(
            content,
            ""
        )

    def test_enable_inactive_diff(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.restore_hosts(quiet=True, do_not_prompt=True)
        with open(tblock.config.Path.BUILT_HOSTS_BACKUP, "at") as f:
            f.write("#\n")
        tblock.enable_protection(quiet=True, do_not_prompt=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertEqual(
            content,
            ""
        )


class TestUpdateDef(unittest.TestCase):

    def test_update_new(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertNotEqual(
            content,
            ""
        )


class TestRestoreDef(unittest.TestCase):

    def test_restore_new(self):
        _create_env()
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertRaises(
            tblock.exceptions.HostsError,
            tblock.restore_hosts, quiet=True, do_not_prompt=True
        )

    def test_restore_active(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.restore_hosts(quiet=True, do_not_prompt=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertEqual(
            content,
            ""
        )


class TestRemoveDef(unittest.TestCase):

    def test_remove_new(self):
        _create_env()
        tblock.hosts.remove_from_hosts({"example.org": None}, quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertEqual(
            content,
            ""
        )

    def test_remove_active(self):
        _create_env()
        tblock.block_domains(["example.org"], quiet=True, do_not_prompt=True, also_update_hosts=True)
        tblock.hosts.remove_from_hosts({"example.org": None}, quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertFalse(
            bool("example.org" in content)
        )

    def test_remove_inactive(self):
        _create_env()
        tblock.block_domains(["example.org"], quiet=True, do_not_prompt=True, also_update_hosts=True)
        tblock.restore_hosts(quiet=True, do_not_prompt=True)
        tblock.hosts.remove_from_hosts({"example.org": None}, quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertEqual(
            content,
            ""
        )

    def test_remove_active_redirect_ip(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", quiet=True, do_not_prompt=True, also_update_hosts=True)
        tblock.hosts.remove_from_hosts({"example.org": "127.0.0.2"}, quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertFalse(
            bool("example.org" in content)
        )

    def test_remove_active_redirect_ip_diff(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", quiet=True, do_not_prompt=True, also_update_hosts=True)
        tblock.hosts.remove_from_hosts({"example.org": None}, quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertTrue(
            bool("example.org" in content)
        )


class TestAddDef(unittest.TestCase):

    def test_add_new(self):
        _create_env()
        tblock.hosts.add_to_hosts(["example.org"], quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertEqual(
            content,
            ""
        )

    def test_add_active(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.hosts.add_to_hosts(["example.org"], quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertTrue(
            bool("example.org" in content)
        )

    def test_add_inactive(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.restore_hosts(quiet=True, do_not_prompt=True)
        tblock.hosts.add_to_hosts(["example.org"], quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertEqual(
            content,
            ""
        )

    def test_add_active_redirect_ip(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.hosts.add_to_hosts(["example.org"], ip="127.0.0.2", quiet=True)
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
        self.assertTrue(
            bool("example.org" in content and "127.0.0.2" in content)
        )


if __name__ == "__main__":
    unittest.main()

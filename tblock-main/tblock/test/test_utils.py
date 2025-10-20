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
import hashlib
import sys
import time
import tblock
import tblock.utils
import tblock.exceptions
import os
import unittest
from . import _create_env
import subprocess
import requests

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


class TestDbLockedDef(unittest.TestCase):

    def test_locked(self):
        _create_env()
        tblock.utils.lock_db()
        self.assertTrue(
            tblock.utils.db_is_locked()
        )

    def test_unlocked(self):
        _create_env()
        self.assertFalse(
            tblock.utils.db_is_locked()
        )


class TestLockDbDef(unittest.TestCase):

    def test_unlocked(self):
        _create_env()
        tblock.utils.lock_db()
        self.assertTrue(
            tblock.utils.db_is_locked()
        )

    def test_locked(self):
        _create_env()
        tblock.utils.lock_db()
        self.assertRaises(
            tblock.exceptions.DatabaseLockedError,
            tblock.utils.lock_db
        )


class TestUnlockDbDef(unittest.TestCase):

    def test_locked(self):
        _create_env()
        tblock.utils.lock_db()
        tblock.utils.unlock_db()
        self.assertFalse(
            tblock.utils.db_is_locked()
        )

    def test_unlocked(self):
        _create_env()
        tblock.utils.unlock_db()
        self.assertFalse(
            tblock.utils.db_is_locked()
        )


class TestValidIpDef(unittest.TestCase):

    def test_valid_ipv4(self):
        self.assertTrue(
            tblock.utils.is_valid_ip("127.0.0.1")
        )

    def test_valid_ipv6(self):
        self.assertTrue(
            tblock.utils.is_valid_ip("ff02::2")
        )

    def test_invalid_ipv4(self):
        self.assertFalse(
            tblock.utils.is_valid_ip("0.0.0.257")
        )

    def test_invalid_ipv6(self):
        self.assertFalse(
            tblock.utils.is_valid_ip("ff02:2")
        )

    def test_invalid_ip(self):
        self.assertFalse(
            tblock.utils.is_valid_ip("example.org")
        )


class TestWildcards(unittest.TestCase):

    def test_contains(self):
        self.assertTrue(
            tblock.utils.contains_wildcards("example.*")
        )

    def test_not_contains(self):
        self.assertFalse(
            tblock.utils.contains_wildcards("example.org")
        )


class TestUrl(unittest.TestCase):

    def test_valid_http(self):
        self.assertTrue(
            tblock.utils.is_url("http://example.org")
        )

    def test_valid_https(self):
        self.assertTrue(
            tblock.utils.is_url("https://example.org")
        )

    def test_valid_ftp(self):
        self.assertTrue(
            tblock.utils.is_url("ftp://example.org")
        )

    def test_valid_sftp(self):
        self.assertTrue(
            tblock.utils.is_url("sftp://example.org")
        )

    def test_invalid_protocol_ssh(self):
        self.assertFalse(
            tblock.utils.is_url("ssh://example.org")
        )

    def test_invalid_host(self):
        self.assertFalse(
            tblock.utils.is_url("example.org")
        )


class TestFetchFileDef(unittest.TestCase):

    def test_fetch_http_200(self):
        _create_env()
        fetch = tblock.utils.fetch_file("http://127.0.0.1:12345/test-list.txt", description="", quiet=True,
                                        output_file=os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"))
        if not fetch:
            self.skipTest("server not running")
        self.assertTupleEqual(
            (True, True),
            (
                fetch, os.path.isfile(os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"))
            )
        )

    def test_fetch_http_400(self):
        _create_env()
        self.assertFalse(
            tblock.utils.fetch_file("http://127.0.0.1:12345/null", description="", quiet=True,
                                    output_file=os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"))
        )

    def test_fetch_local_200(self):
        _create_env()
        self.assertTupleEqual(
            (True, True),
            (
                tblock.utils.fetch_file(os.path.join(os.path.dirname(__file__), "srv", "test-list.txt"),
                                        description="", quiet=True,
                                        output_file=os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt")),
                os.path.isfile(os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"))
            )
        )

    def test_fetch_local_400(self):
        _create_env()
        self.assertFalse(
            tblock.utils.fetch_file(os.path.join(os.path.dirname(__file__), "srv", "null"),
                                    description="", quiet=True,
                                    output_file=os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"))
        )

    def test_fetch_http_200_sha512(self):
        _create_env()
        with open(os.path.join(os.path.dirname(__file__), "srv", "test-list.txt"), 'rb') as r:
            hash = hashlib.sha512(r.read()).hexdigest()
        fetch = tblock.utils.fetch_file("http://127.0.0.1:12345/test-list.txt", description="", quiet=True,
                                        output_file=os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"),
                                        sha512sum=hash)
        if not fetch:
            self.skipTest("server not running")
        self.assertTupleEqual(
            (True, True),
            (
                fetch, os.path.isfile(os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"))
            )
        )

    def test_fetch_http_200_sha512_wrong(self):
        _create_env()
        hash = ""
        fetch = tblock.utils.fetch_file("http://127.0.0.1:12345/test-list.txt", description="", quiet=True,
                                        output_file=os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"),
                                        sha512sum=hash)
        path = os.path.isfile(os.path.join(tblock.config.Path.TMP_DIR, "test-list.txt"))
        if not path:
            self.skipTest("server not running")
        self.assertTupleEqual(
            (False, True),
            (fetch, path)
        )


if __name__ == "__main__":
    unittest.main()

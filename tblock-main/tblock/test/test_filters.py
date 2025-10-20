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
import shutil

import tblock
import tblock.exceptions
import os
import unittest
from . import _create_env
import subprocess

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

tblock.config.Var.REPO_MIRRORS = ["http://127.0.0.1:12345/index.json"]


class TestFilterClass(unittest.TestCase):
    def test_method_init(self):
        _create_env()
        f = tblock.Filter("test", quiet=True)
        self.assertTupleEqual(
            (
                f.id,
                f.exists,
                f.source,
                f.source_exists,
                f.metadata,
                f.subscribing,
                f.on_repo,
                f.mirrors,
                f.syntax,
                f.rules_count,
            ),
            ("test", False, None, False, {}, False, False, {}, None, 0),
        )

    def test_method_retrieve_mirror(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        get = f.retrieve_mirror("http://127.0.0.1:12345/test-list.txt", None)
        self.assertTupleEqual((get, os.path.isfile(f.tmp_file)), (True, True))

    def test_method_retrieve_mirror_xz(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        get = f.retrieve_mirror("http://127.0.0.1:12345/test-list.txt.xz", "xz")
        self.assertTupleEqual((get, os.path.isfile(f.tmp_file)), (True, True))

    def test_method_retrieve_mirror_gzip(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        get = f.retrieve_mirror("http://127.0.0.1:12345/test-list.txt.gz", "gzip")
        self.assertTupleEqual((get, os.path.isfile(f.tmp_file)), (True, True))

    def test_method_cache_exists_false(self):
        _create_env()
        f = tblock.Filter("test-list", quiet=True)
        self.assertFalse(f.cache_exists())

    def test_method_cache_exists_true(self):
        _create_env()
        f = tblock.Filter("test-list", quiet=True)
        open(f.cache_file, "wt").close()
        self.assertTrue(f.cache_exists())

    def test_method_cache_is_up_to_date_true(self):
        _create_env()
        f = tblock.Filter("test-list")
        open(f.cache_file, "wt").close()
        shutil.copy(f.cache_file, f.tmp_file)
        self.assertTrue(f.cache_is_up_to_date())

    def test_method_cache_is_up_to_date_false(self):
        _create_env()
        f = tblock.Filter("test-list")
        open(f.cache_file, "wt").close()
        with open(f.tmp_file, "wt") as w:
            w.write("\n")
        self.assertFalse(f.cache_is_up_to_date())

    def test_method_get_rules_count(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        tblock.subscribe(["test-list"], quiet=True, do_not_prompt=True)
        f = tblock.Filter("test-list")
        self.assertEqual(f.get_rules_count(), 6)

    def test_method_get_rules_count_0(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        self.assertEqual(f.get_rules_count(), 0)

    def test_method_get_rules_count_none(self):
        _create_env()
        f = tblock.Filter("test-list")
        self.assertRaises(tblock.exceptions.FilterError, f.get_rules_count)

    def test_method_delete_cache(self):
        _create_env()
        f = tblock.Filter("test-list", quiet=True)
        open(f.cache_file, "wt").close()
        f.delete_cache()
        self.assertFalse(os.path.isfile(f.cache_file))

    def test_method_delete_cache_none(self):
        _create_env()
        f = tblock.Filter("test-list", quiet=True)
        f.delete_cache()
        self.assertFalse(os.path.isfile(f.cache_file))

    def test_method_retrieve(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        self.assertTrue(os.path.isfile(f.tmp_file))

    def test_method_retrieve_unknown(self):
        _create_env()
        f = tblock.Filter("test-list", quiet=True)
        self.assertRaises(tblock.exceptions.FilterError, f.retrieve)

    def test_method_retrieve_fallback_mirror(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.source = "http://127.0.0.1:12345/null"
        f.mirrors = {"http://127.0.0.1:12345/test-list.txt": {"compressions": None}}
        f.retrieve()
        self.assertTrue(os.path.isfile(f.tmp_file))

    def test_method_retrieve_fallback_mirror_xz(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.source = "http://127.0.0.1:12345/null"
        f.mirrors = {"http://127.0.0.1:12345/test-list.txt.xz": {"compressions": "xz"}}
        f.retrieve()
        self.assertTrue(os.path.isfile(f.tmp_file))

    def test_method_retrieve_fallback_mirror_gzip(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.source = "http://127.0.0.1:12345/null"
        f.mirrors = {
            "http://127.0.0.1:12345/test-list.txt.gz": {"compressions": "gzip"}
        }
        f.retrieve()
        self.assertTrue(os.path.isfile(f.tmp_file))

    def test_method_retrieve_mirror_fallback_local_cache(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        f.update()
        f.source = "http://127.0.0.1:12345/null"
        f.mirrors = {}
        f.retrieve()
        self.assertTrue(os.path.isfile(f.tmp_file))

    def test_method_retrieve_mirror_fail(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.source = "http://127.0.0.1:12345/null"
        f.mirrors = {}
        self.assertRaises(tblock.exceptions.FilterError, f.retrieve)

    def test_method_update(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        f.update()
        r1 = tblock.Rule("example.org")
        r2 = tblock.Rule("block.example.com")
        r3 = tblock.Rule("allow.example.org")
        r4 = tblock.Rule("redirect.example.com")
        self.assertTupleEqual(
            (r1.filter_id, r2.filter_id, r3.exists, r4.exists),
            ("test-list", "test-list", True, False),
        )

    def test_method_update_then_overwrite(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError as err:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        f.update()
        f2 = tblock.Filter("test-list-2", quiet=True)
        f2.retrieve()
        f2.subscribe()
        f2.update()
        r1 = tblock.Rule("allow.example.org")
        r2 = tblock.Rule("example.org")
        r3 = tblock.Rule("allow.example.com")
        r4 = tblock.Rule("block.example.org")
        # Check that allowing rules are not being overwritten by allowing rules from other filter lists
        assert r1.filter_id == "test-list"
        assert r1.policy == "A"
        # Check that blocking rules are being overwritten by allowing rules from other filter lists
        assert r2.filter_id == "test-list-2"
        assert r2.policy == "A"
        # Check that allowing rules are not being overwritten by blocking rules from other filter lists
        assert r3.filter_id == "test-list"
        assert r3.policy == "A"
        # Check that blocking rules are not being overwritten by blocking rules from other filter lists
        assert r4.filter_id == "test-list"
        assert r4.policy == "B"

    def test_method_update_not_subscribing_not_retrieved(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        self.assertRaises(tblock.exceptions.FilterError, f.update)

    def test_method_update_not_subscribing(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        self.assertRaises(tblock.exceptions.FilterError, f.update)

    def test_method_update_up_to_date(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        f.update()
        f.retrieve()
        status = f.cache_is_up_to_date()
        f.update()
        self.assertTrue((os.path.isfile(f.tmp_file), status))

    def test_method_delete_all_rules(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        f.update()
        rb = tblock.Rule("example.org").filter_id
        f.delete_all_rules()
        self.assertTupleEqual(
            (rb, tblock.Rule("example.org").exists, f.get_rules_count()),
            ("test-list", False, 0),
        )

    def test_method_delete_all_rules_not_subscribing(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.delete_all_rules()
        self.assertFalse(f.subscribing)

    def test_method_subscribe(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        self.assertTupleEqual((f.subscribing, f.get_rules_count()), (True, 0))

    def test_method_subscribe_not_retrieved(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        self.assertRaises(tblock.exceptions.FilterError, f.subscribe)

    def test_method_subscribe_non_existing(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("null", quiet=True)
        self.assertRaises(tblock.exceptions.FilterError, f.subscribe)

    def test_method_add_custom(self):
        _create_env()
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        f.add_custom()
        self.assertTupleEqual(
            (f.exists, f.on_repo, f.subscribing), (True, False, False)
        )

    def test_method_add_custom_user_id_priority(self):
        _create_env()
        f = tblock.Filter(
            tblock.USER_RULE_PRIORITY,
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        self.assertRaises(tblock.exceptions.FilterError, f.add_custom)

    def test_method_add_custom_file_not_found(self):
        _create_env()
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=os.path.join(os.path.dirname(__file__), "srv", "null"),
        )
        self.assertRaises(FileNotFoundError, f.add_custom)

    def test_method_add_custom_conflict_id(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter(
            "test-list",
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        self.assertRaises(tblock.exceptions.FilterError, f.add_custom)

    def test_method_add_custom_conflict_source(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=tblock.Filter("test-list").source,
        )
        self.assertRaises(tblock.exceptions.FilterError, f.add_custom)

    def test_method_add_custom_no_source(self):
        _create_env()
        f = tblock.Filter("test-list-local", quiet=True)
        self.assertRaises(tblock.exceptions.FilterError, f.add_custom)

    def test_method_unsubscribe(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        f.update()
        f.unsubscribe()
        rb = tblock.Rule("example.org")
        self.assertTupleEqual(
            (f.subscribing, f.on_repo, rb.exists), (False, True, False)
        )

    def test_method_unsubscribe_custom(self):
        _create_env()
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        f.add_custom()
        f.retrieve()
        f.subscribe()
        f.update()
        f.unsubscribe()
        rb = tblock.Rule("example.org")
        self.assertTupleEqual(
            (f.subscribing, f.on_repo, rb.exists, f.exists),
            (False, False, False, False),
        )

    def test_method_unsubscribe_not_subscribing(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.unsubscribe()
        self.assertTupleEqual((f.subscribing, f.on_repo), (False, True))

    def test_method_unsubscribe_custom_not_subscribing(self):
        _create_env()
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        f.add_custom()
        f.unsubscribe()
        self.assertTupleEqual(
            (f.subscribing, f.on_repo, f.exists), (False, False, False)
        )

    def test_method_unsubscribe_custom_non_existing(self):
        _create_env()
        f = tblock.Filter("test-list", quiet=True)
        f.unsubscribe()
        self.assertTupleEqual(
            (f.subscribing, f.on_repo, f.exists), (False, False, False)
        )

    def test_method_rename(self):
        _create_env()
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        f.add_custom()
        f.retrieve()
        f.subscribe()
        f.update()
        f.rename_custom("test-list-renamed")
        self.assertTupleEqual(
            (tblock.Rule("example.org").filter_id, f.id),
            ("test-list-renamed", "test-list-renamed"),
        )

    def test_method_rename_conflict_id(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        f.add_custom()
        f.retrieve()
        f.subscribe()
        f.update()
        self.assertRaises(tblock.exceptions.FilterError, f.rename_custom, "test-list")

    def test_method_rename_same_id(self):
        _create_env()
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        f.add_custom()
        f.retrieve()
        f.subscribe()
        f.update()
        self.assertRaises(
            tblock.exceptions.FilterError, f.rename_custom, "test-list-local"
        )

    def test_method_rename_not_custom(self):
        _create_env()
        try:
            tblock.sync_filter_list_repo(quiet=True)
        except tblock.exceptions.RepoError:
            self.skipTest("server not running")
        f = tblock.Filter("test-list", quiet=True)
        f.retrieve()
        f.subscribe()
        f.update()
        f.rename_custom("test-list-local")
        self.assertEqual(f.id, "test-list")

    def test_method_rename_user_id_priority(self):
        _create_env()
        f = tblock.Filter(
            "test-list-local",
            quiet=True,
            custom_source=os.path.join(
                os.path.dirname(__file__), "srv", "test-list.txt"
            ),
        )
        f.add_custom()
        f.retrieve()
        f.subscribe()
        f.update()
        self.assertRaises(
            tblock.exceptions.FilterError,
            f.rename_custom,
            filter_id=tblock.USER_RULE_PRIORITY,
        )


if __name__ == "__main__":
    unittest.main()

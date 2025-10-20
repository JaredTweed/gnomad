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
import multiprocessing
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


class TestRuleClass(unittest.TestCase):

    def test_method_init(self):
        _create_env()
        r = tblock.Rule("example.org")
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", False, None, None, None, False)
        )

    def test_method_add_allow_new(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.ALLOW, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_allow_new_wildcards(self):
        _create_env()
        r = tblock.Rule("example.*")
        r.add(tblock.ALLOW, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.*", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_block_new(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.BLOCK, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_block_new_wildcards(self):
        _create_env()
        r = tblock.Rule("example.*")
        self.assertRaises(
            tblock.exceptions.RuleError,
            r.add, policy=tblock.BLOCK, quiet=True
        )

    def test_method_add_redirect_new(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.REDIRECT, tblock.USER_RULE_PRIORITY, "127.0.0.2", True)
        )

    def test_method_add_redirect_new_wildcards(self):
        _create_env()
        r = tblock.Rule("example.*")
        self.assertRaises(
            tblock.exceptions.RuleError,
            r.add, policy=tblock.REDIRECT, ip="127.0.0.2", quiet=True
        )

    def test_method_add_redirect_new_no_ip(self):
        _create_env()
        r = tblock.Rule("example.org")
        self.assertRaises(
            tblock.exceptions.RuleError,
            r.add, policy=tblock.REDIRECT, quiet=True
        )

    def test_method_add_redirect_new_invalid_ip(self):
        _create_env()
        r = tblock.Rule("example.org")
        self.assertRaises(
            tblock.exceptions.RuleError,
            r.add, policy=tblock.REDIRECT, ip="this is not a valid ip address", quiet=True
        )

    def test_method_remove_new(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.remove(quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", False, None, None, None, False)
        )

    def test_method_add_allow_overwrite_allow(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.ALLOW, quiet=True)
        r.add(tblock.ALLOW, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_allow_overwrite_allow_wildcards(self):
        _create_env()
        r = tblock.Rule("example.*")
        r.add(tblock.ALLOW, quiet=True)
        r = tblock.Rule("example.org")
        r.add(tblock.ALLOW, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_allow_overwrite_block(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.BLOCK, quiet=True)
        r.add(tblock.ALLOW, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_allow_overwrite_redirect(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        r.add(tblock.ALLOW, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_block_overwrite_allow(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.ALLOW, quiet=True)
        r.add(tblock.BLOCK, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_block_overwrite_allow_wildcards(self):
        _create_env()
        r = tblock.Rule("example.*")
        r.add(tblock.ALLOW, quiet=True)
        r = tblock.Rule("example.org")
        r.add(tblock.BLOCK, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", False, None, None, None, False)
        )

    def test_method_add_block_overwrite_block(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.BLOCK, quiet=True)
        r.add(tblock.BLOCK, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_block_overwrite_redirect(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        r.add(tblock.BLOCK, quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, None, True)
        )

    def test_method_add_redirect_overwrite_allow(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.ALLOW, quiet=True)
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.REDIRECT, tblock.USER_RULE_PRIORITY, "127.0.0.2", True)
        )

    def test_method_add_redirect_overwrite_allow_wildcards(self):
        _create_env()
        r = tblock.Rule("example.*")
        r.add(tblock.ALLOW, quiet=True)
        r = tblock.Rule("example.org")
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", False, None, None, None, False)
        )

    def test_method_add_redirect_overwrite_block(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.BLOCK, quiet=True)
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.REDIRECT, tblock.USER_RULE_PRIORITY, "127.0.0.2", True)
        )

    def test_method_add_redirect_overwrite_redirect(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.REDIRECT, tblock.USER_RULE_PRIORITY, "127.0.0.2", True)
        )

    def test_method_add_redirect_overwrite_redirect_diff_ip(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.REDIRECT, ip="127.0.0.1", quiet=True)
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", True, tblock.REDIRECT, tblock.USER_RULE_PRIORITY, "127.0.0.2", True)
        )

    def test_method_remove_overwrite_allow(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.ALLOW, quiet=True)
        r.remove(quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", False, None, None, None, False)
        )

    def test_method_remove_overwrite_block(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.BLOCK, quiet=True)
        r.remove(quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", False, None, None, None, False)
        )

    def test_method_remove_overwrite_redirect(self):
        _create_env()
        r = tblock.Rule("example.org")
        r.add(tblock.REDIRECT, ip="127.0.0.2", quiet=True)
        r.remove(quiet=True)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, r.ip, r.is_user_rule),
            ("example.org", False, None, None, None, False)
        )

    def test_method_wildcard_exists_true_match(self):
        _create_env()
        r = tblock.Rule("example.*")
        r.add(tblock.ALLOW, quiet=True)
        r = tblock.Rule("example.org")
        self.assertEqual(
            r.wildcard_exists(),
            True
        )

    def test_method_wildcard_exists_true_no_match(self):
        _create_env()
        r = tblock.Rule("example.*")
        r.add(tblock.ALLOW, quiet=True)
        r = tblock.Rule("ns.example.org")
        self.assertEqual(
            r.wildcard_exists(),
            False
        )

    def test_method_wildcard_exists_false(self):
        _create_env()
        r = tblock.Rule("example.org")
        self.assertEqual(
            r.wildcard_exists(),
            False
        )


class TestAllowDef(unittest.TestCase):

    def test_allow_new(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_new_not_enabled(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_new_update_hosts(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_allow(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_block(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_redirect(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_allow_update_hosts(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_block_update_hosts(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_redirect_update_hosts(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_allow_wildcards(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.*"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_block_wildcards(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.*"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", False, None, None, False)
        )

    def test_allow_overwrite_redirect_wildcards(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.*"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", False, None, None, False)
        )

    def test_allow_overwrite_allow_wildcards_update_hosts(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.*"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.ALLOW, tblock.USER_RULE_PRIORITY, False)
        )

    def test_allow_overwrite_block_wildcards_update_hosts(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.*"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", False, None, None, False)
        )

    def test_allow_overwrite_redirect_wildcards_update_hosts(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.allow_domains(["example.*"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", False, None, None, False)
        )


class TestBlockDef(unittest.TestCase):

    def test_block_new(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, True)
        )

    def test_block_new_not_enabled(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, False)
        )

    def test_block_new_update_hosts(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, True)
        )

    def test_block_overwrite_allow(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, True)
        )

    def test_block_overwrite_block(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, True)
        )

    def test_block_overwrite_redirect(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" not in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, False)  # This should be changed soon
        )

    def test_block_overwrite_allow_update_hosts(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, True)
        )

    def test_block_overwrite_block_update_hosts(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, True)
        )

    def test_block_overwrite_redirect_update_hosts(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" not in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", True, tblock.BLOCK, tblock.USER_RULE_PRIORITY, True)
        )

    def test_block_overwrite_allow_wildcards(self):
        _create_env()
        tblock.allow_domains(["example.*"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            added = bool("example.org" in f.read())
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", False, None, None, False)
        )


class TestRedirectDef(unittest.TestCase):

    def test_redirect_new(self):
        _create_env()
        tblock.update_hosts(quiet=True, do_not_prompt=True)
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.2", tblock.USER_RULE_PRIORITY, True)
        )

    def test_redirect_new_not_enabled(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.2", tblock.USER_RULE_PRIORITY, False)
        )

    def test_redirect_new_update_hosts(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.2", tblock.USER_RULE_PRIORITY, True)
        )

    def test_redirect_overwrite_allow(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.2", tblock.USER_RULE_PRIORITY, True)
        )

    def test_redirect_overwrite_block(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.2", tblock.USER_RULE_PRIORITY, True)
        )

    def test_redirect_overwrite_redirect(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.redirect_domains(["example.org"], ip="127.0.0.3", do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" not in content and "127.0.0.3" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.3", tblock.USER_RULE_PRIORITY, False)  # This should be changed soon
        )

    def test_redirect_overwrite_allow_update_hosts(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.2", tblock.USER_RULE_PRIORITY, True)
        )

    def test_redirect_overwrite_block_update_hosts(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.2", tblock.USER_RULE_PRIORITY, True)
        )

    def test_redirect_overwrite_redirect_update_hosts(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.redirect_domains(["example.org"], ip="127.0.0.3", do_not_prompt=True, quiet=True, also_update_hosts=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" not in content and "127.0.0.3" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.ip, r.filter_id, added),
            ("example.org", True, tblock.REDIRECT, "127.0.0.3", tblock.USER_RULE_PRIORITY, True)
        )

    def test_redirect_overwrite_allow_wildcards(self):
        _create_env()
        tblock.allow_domains(["example.*"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True)
        r = tblock.Rule("example.org")
        with open(tblock.config.Path.HOSTS, "rt") as f:
            content = f.read()
            added = bool("example.org" in content and "127.0.0.2" in content)
        self.assertTupleEqual(
            (r.domain, r.exists, r.policy, r.filter_id, added),
            ("example.org", False, None, None, False)
        )


class TestCheckWildcardDef(unittest.TestCase):

    def test_match_zero(self):
        _create_env()
        cnt = multiprocessing.Value('i', 0)
        quiet_mode = True
        tblock.rules.init_globals(cnt, quiet_mode)
        self.assertDictEqual(
            tblock.rules.check_wildcard_domains("example.*"),
            {}
        )

    def test_match_one_allow(self):
        _create_env()
        tblock.allow_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        cnt = multiprocessing.Value('i', 0)
        quiet_mode = True
        tblock.rules.init_globals(cnt, quiet_mode)
        self.assertDictEqual(
            tblock.rules.check_wildcard_domains(("example.*",)),
            {}
        )

    def test_match_one_block(self):
        _create_env()
        tblock.block_domains(["example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        cnt = multiprocessing.Value('i', 0)
        quiet_mode = True
        tblock.rules.init_globals(cnt, quiet_mode)
        self.assertDictEqual(
            tblock.rules.check_wildcard_domains(("example.*",)),
            {"example.org": None}
        )

    def test_match_one_redirect(self):
        _create_env()
        tblock.redirect_domains(["example.org"], ip="127.0.0.2", do_not_prompt=True, quiet=True, also_update_hosts=True)
        cnt = multiprocessing.Value('i', 0)
        quiet_mode = True
        tblock.rules.init_globals(cnt, quiet_mode)
        self.assertDictEqual(
            tblock.rules.check_wildcard_domains(("example.*",)),
            {"example.org": "127.0.0.2"}
        )


class TestGetAllRulesDef(unittest.TestCase):

    def test_get_all(self):
        _create_env()
        tblock.block_domains(["example.com", "example.org"], do_not_prompt=True, quiet=True, also_update_hosts=True)
        self.assertListEqual(
            tblock.get_all_rules(),
            ["example.com", "example.org"]
        )


if __name__ == "__main__":
    unittest.main()

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

# Standard modules
import re
import os
import sqlite3
import ipaddress
from urllib3.util import parse_url
import multiprocessing

# Local modules
from .config import Path
from .style import loading_icon, Icon, Font
from .const import USER_RULE_PRIORITY, RulePolicy
from .exceptions import RuleError
from .utils import (
    is_valid_ip,
    prompt_user,
    check_root_access,
    is_valid_domain,
    lock_db,
    unlock_db,
)
from .hosts import update_hosts, remove_from_hosts, add_to_hosts


class Rule:
    def __init__(self, domain: str, user_rule: bool = False) -> None:
        """
        User rule object
        :param domain: The domain to use
        :param user_rule: The rule must strictly be a user rule
        """
        self.domain = parse_url(domain).host
        # Fetch rule data from the database
        with sqlite3.connect(Path.RULES_DATABASE) as conn:
            data = (
                conn.cursor()
                .execute('SELECT "policy", "ip" FROM r WHERE domain=?;', (self.domain,))
                .fetchone()
            )
        self.exists = bool(data)
        self.policy = data[0] if data else None
        self.filter_id = "!user" if data else None
        self.ip = data[1] if data else None
        self.is_user_rule = True
        if not data and not user_rule:
            with sqlite3.connect(Path.DATABASE) as conn:
                data = (
                    conn.cursor()
                    .execute(
                        'SELECT "policy", "filter_id", "ip" FROM rules WHERE domain=?;',
                        (self.domain,),
                    )
                    .fetchone()
                )
            self.exists = bool(data)
            self.policy = data[0] if data else None
            self.filter_id = data[1] if data else None
            self.ip = data[2] if data else None
            self.is_user_rule = False

    def wildcard_exists(self) -> bool:
        with sqlite3.connect(Path.RULES_DATABASE) as conn:
            data = conn.cursor().execute(
                "SELECT domain FROM r WHERE domain LIKE '%*%';"
            )
        for rule in data:
            if re.match(
                re.compile(rule[0].replace(".", "\\.").replace("*", ".*")), self.domain
            ):
                return True
        with sqlite3.connect(Path.DATABASE) as conn:
            data2 = conn.cursor().execute(
                "SELECT domain FROM rules WHERE domain LIKE '%*%';"
            )
        for rule in data2:
            if re.match(
                re.compile(rule[0].replace(".", "\\.").replace("*", ".*")), self.domain
            ):
                return True
        else:
            return False

    def add(self, policy: str, ip: str = None, quiet: bool = False) -> None:
        """
        Add a user rule inside the database
        :param policy: The policy to use (RulePolicy.ALLOW, RulePolicy.BLOCK, RulePolicy.REDIRECT)
        :param ip: Optional. The bind address domains should be redirected to (only when the policy is redirect)
        :param quiet: Optional. Do not display an output (false by default)
        """
        if (
            self.exists
            and self.policy == policy
            and self.ip == ip
            and self.filter_id == USER_RULE_PRIORITY
        ):
            if not quiet:
                print(
                    f" {Icon.WARNING} Exact same rule already exists for domain: {self.domain}"
                )
        elif not is_valid_domain(
            self.domain, allow_wildcards=bool(policy == RulePolicy.ALLOW)
        ):
            raise RuleError("Invalid domain rule: {0}".format(self.domain))
        else:
            if (
                policy == RulePolicy.ALLOW
                or policy == RulePolicy.BLOCK
                or policy == RulePolicy.REDIRECT
            ):
                if policy != RulePolicy.REDIRECT or is_valid_ip(ip):
                    __msg = "Adding rule for domain: {0}".format(self.domain)
                    if not quiet:
                        print(f" {loading_icon(1)} {__msg}", end="\r")

                    if policy == RulePolicy.ALLOW or not self.wildcard_exists():
                        if policy == RulePolicy.REDIRECT:
                            ip_address = ipaddress.ip_address(ip)
                            if self.exists and self.filter_id == USER_RULE_PRIORITY:
                                with sqlite3.connect(Path.RULES_DATABASE) as conn:
                                    conn.cursor().execute(
                                        "UPDATE r SET policy=?, ip=? WHERE domain=?;",
                                        (policy, ip_address.compressed, self.domain),
                                    )
                                    conn.commit()
                                self.__init__(self.domain)
                            else:
                                if self.exists:
                                    with sqlite3.connect(Path.DATABASE) as conn:
                                        conn.cursor().execute(
                                            "DELETE FROM rules WHERE domain=?",
                                            (self.domain,),
                                        )
                                with sqlite3.connect(Path.RULES_DATABASE) as conn:
                                    conn.cursor().execute(
                                        "INSERT INTO r (domain, policy, ip)"
                                        "VALUES (?, ?, ?);",
                                        (self.domain, policy, ip_address.compressed),
                                    )
                                    conn.commit()
                                self.__init__(self.domain)

                        else:
                            if self.exists and self.filter_id == USER_RULE_PRIORITY:
                                with sqlite3.connect(Path.RULES_DATABASE) as conn:
                                    conn.cursor().execute(
                                        "UPDATE r SET policy=?, ip=? WHERE domain=?;",
                                        (policy, None, self.domain),
                                    )
                                    conn.commit()
                                self.__init__(self.domain)
                            else:
                                if self.exists:
                                    with sqlite3.connect(Path.DATABASE) as conn:
                                        conn.cursor().execute(
                                            "DELETE FROM rules WHERE domain=?",
                                            (self.domain,),
                                        )
                                with sqlite3.connect(Path.RULES_DATABASE) as conn:
                                    conn.cursor().execute(
                                        "INSERT INTO r (domain, policy, ip)"
                                        "VALUES (?, ?, ?);",
                                        (self.domain, policy, None),
                                    )
                                    conn.commit()
                                self.__init__(self.domain)
                        if not quiet:
                            print(f" {Icon.SUCCESS} {__msg}")
                    else:
                        if not quiet:
                            print(f" {Icon.ERROR} {__msg}")
                            print(
                                f" {Icon.WARNING} Wildcard rule already allows domain: {self.domain}"
                            )

                else:
                    raise RuleError("invalid ip address: {0}".format(ip))
            else:
                raise RuleError("invalid rule policy: {0}".format(policy))

    def remove(self, quiet: bool = False) -> None:
        """
        Remove a user rule from the database
        :param quiet: Optional. Do not display an output (false by default)
        """
        if not self.exists or not self.is_user_rule:
            if not quiet:
                print(f" {Icon.WARNING} No user rule exists for domain: {self.domain}")
        else:
            __msg = "Deleting rule for domain: {0}".format(self.domain)
            if not quiet:
                print(f" {loading_icon(1)} {__msg}", end="\r")
            with sqlite3.connect(Path.RULES_DATABASE) as conn:
                conn.cursor().execute("DELETE FROM r WHERE domain=?;", (self.domain,))
                conn.commit()
            self.__init__(self.domain)
            if not quiet:
                print(f" {Icon.SUCCESS} {__msg}")


def __remove_allowed_matches(quiet: bool = False) -> dict:
    if not quiet:
        print(f"{Font.BOLD}==> Cleaning database{Font.DEFAULT}")
    conn = sqlite3.connect(Path.DATABASE)
    cursor = conn.cursor()
    wildcards = cursor.execute(
        'SELECT domain FROM rules WHERE policy=? AND domain LIKE "%*%";',
        (RulePolicy.ALLOW,),
    ).fetchall()
    conn.close()
    conn = sqlite3.connect(Path.RULES_DATABASE)
    cursor = conn.cursor()
    wildcards += cursor.execute(
        'SELECT domain FROM r WHERE policy=? AND domain LIKE "%*%";',
        (RulePolicy.ALLOW,),
    )
    conn.close()

    cnt = multiprocessing.Value("i", 0)

    with multiprocessing.Pool(initializer=init_globals, initargs=(cnt, quiet)) as pool:
        wildcards_matches = pool.map(check_wildcard_domains, wildcards)
    if not quiet:
        print(
            " {0} Checking wildcards rules: {1}/{2}".format(
                Icon.SUCCESS, cnt.value, len(wildcards)
            )
        )
    matches = {}
    for row in wildcards_matches:
        matches.update(row)
    return matches


def init_globals(counter, quiet):
    global cnt
    cnt = counter
    global quiet_mode
    quiet_mode = quiet


def check_wildcard_domains(i) -> dict:
    matches = {}
    cnt.value += 1
    if not quiet_mode:
        print(
            " {0} Checking wildcards rules: {1}".format(
                loading_icon(cnt.value), cnt.value
            ),
            end="\r",
        )
    conn = sqlite3.connect(Path.DATABASE)
    cursor = conn.cursor()
    query = cursor.execute(
        "SELECT domain, ip FROM rules WHERE domain LIKE ? AND policy != ?;",
        (i[0].replace("*", "%"), RulePolicy.ALLOW),
    ).fetchall()
    for q in query:
        cursor.execute("DELETE FROM rules WHERE domain=?;", (q[0],))
        matches[q[0]] = q[1]
    conn.commit()
    conn.close()
    conn = sqlite3.connect(Path.RULES_DATABASE)
    cursor = conn.cursor()
    query = cursor.execute(
        "SELECT domain, ip FROM r WHERE domain LIKE ? AND policy != ?;",
        (i[0].replace("*", "%"), RulePolicy.ALLOW),
    ).fetchall()
    for q in query:
        cursor.execute("DELETE FROM r WHERE domain=?;", (q[0],))
        matches[q[0]] = q[1]
    conn.commit()
    conn.close()
    return matches


def allow_domains(
    domains: list,
    do_not_prompt: bool = False,
    force: bool = False,
    quiet: bool = False,
    also_update_hosts: bool = False,
) -> None:
    """
    Add allowing user rules for a provided list of domains
    :param domains: The list of domains to allow
    :param do_not_prompt: Optional. Do not prompt the user before adding rules (false by default)
    :param force: Optional. Force adding rule, even if the exact same rule already exists
    :param quiet: Optional. Do not display an output (false by default)
    :param also_update_hosts: Optional. Update hosts file after updating filter lists (true by default)
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    lock_db()

    # Prompt the user before continuing
    if do_not_prompt or prompt_user(
        "You are about to allow the following domains:", domains
    ):
        wildcards = False
        # Add rules
        domains_list = {}
        if not quiet:
            print(f"{Font.BOLD}==> Adding rules{Font.DEFAULT}")
        for d in domains:
            rule_object = Rule(d)
            domains_list[d] = Rule(d).ip
            rule_object.add(RulePolicy.ALLOW, quiet=quiet)
            if "*" in list(d):
                wildcards = True
        if wildcards:
            matches = __remove_allowed_matches(quiet)
        else:
            matches = {}
        if also_update_hosts:
            update_hosts(quiet=quiet)
        else:
            remove_from_hosts({**domains_list, **matches}, quiet=quiet)

    # Unlock the database
    unlock_db()


def block_domains(
    domains: list,
    do_not_prompt: bool = False,
    force: bool = False,
    quiet: bool = False,
    also_update_hosts: bool = False,
) -> None:
    """
    Add blocking user rules for a provided list of domains
    :param domains: The list of domains to block
    :param do_not_prompt: Optional. Do not prompt the user before adding rules (false by default)
    :param force: Optional. Force adding rule, even if the exact same rule already exists
    :param quiet: Optional. Do not display an output (false by default)
    :param also_update_hosts: Optional. Update hosts file after updating filter lists (true by default)
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    lock_db()

    # Prompt the user before continuing
    if do_not_prompt or prompt_user(
        "You are about to block the following domains:", domains
    ):
        # Add rules
        if not quiet:
            print(f"{Font.BOLD}==> Adding rules{Font.DEFAULT}")
        domains_to_add = []
        for d in domains:
            rule_object = Rule(d)
            rule_object.add(RulePolicy.BLOCK, quiet=quiet)
            if rule_object.exists:
                domains_to_add.append(d)
        if also_update_hosts:
            update_hosts(quiet=quiet)
        else:
            add_to_hosts(domains_to_add, quiet=quiet)

    # Unlock the database
    unlock_db()


def redirect_domains(
    domains: list,
    ip: str,
    do_not_prompt: bool = False,
    force: bool = False,
    quiet: bool = False,
    also_update_hosts: bool = False,
) -> None:
    """
    Add redirecting user rules for a provided list of domains
    :param domains: The list of domains to redirect
    :param ip: The bind address domains should be redirected to
    :param do_not_prompt: Optional. Do not prompt the user before adding rules (false by default)
    :param force: Optional. Force adding rule, even if the exact same rule already exists
    :param quiet: Optional. Do not display an output (false by default)
    :param also_update_hosts: Optional. Update hosts file after updating filter lists (true by default)
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    lock_db()

    # Prompt the user before continuing
    if do_not_prompt or prompt_user(
        'You are about to redirect the following domains to "{0}":'.format(ip), domains
    ):
        # Add rules
        if not quiet:
            print(f"{Font.BOLD}==> Adding rules{Font.DEFAULT}")
        domains_to_add = []
        for d in domains:
            rule_object = Rule(d)
            rule_object.add(RulePolicy.REDIRECT, ip=ip, quiet=quiet)
            if rule_object.exists:
                domains_to_add.append(d)
        if also_update_hosts:
            update_hosts(quiet=quiet)
        else:
            add_to_hosts(domains_to_add, ip, quiet=quiet)

    # Unlock the database
    unlock_db()


def delete_rules(
    domains: list,
    do_not_prompt: bool = False,
    quiet: bool = False,
    also_update_hosts: bool = False,
) -> None:
    """
    Delete user rules for a provided list of domains
    :param domains: The list of domains to block
    :param do_not_prompt: Optional. Do not prompt the user before adding rules (false by default)
    :param quiet: Optional. Do not display an output (false by default)
    :param also_update_hosts: Optional. Update hosts file after updating filter lists (true by default)
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    lock_db()

    # Prompt the user before continuing
    if do_not_prompt or prompt_user(
        "You are about to delete the rules of the following domains:", domains
    ):
        domains_list = {}
        # Delete rules
        if not quiet:
            print(f"{Font.BOLD}==> Deleting rules{Font.DEFAULT}")
        for d in domains:
            rule_object = Rule(d)
            domains_list[d] = Rule(d).ip
            rule_object.remove(quiet=quiet)
        if also_update_hosts:
            update_hosts(quiet=quiet)
        else:
            remove_from_hosts(domains_list, quiet=quiet)

    # Unlock the database
    unlock_db()


def get_all_rules(
    from_filter_lists: list = None, user_only: bool = False, standard_only: bool = False
) -> list:
    if from_filter_lists and user_only or user_only and standard_only:
        return []
    elif not os.path.isfile(Path.DATABASE):
        raise FileNotFoundError(
            "database does not exist yet. "
            "Please run 'tblock -Y' with admin privileges to create it"
        )
    else:
        output = []
        data2 = None
        if from_filter_lists:
            with sqlite3.connect(Path.DATABASE) as conn:
                for f in from_filter_lists:
                    data = conn.cursor().execute(
                        'SELECT "domain" FROM "rules" WHERE filter_id=? ORDER BY domain ASC;',
                        (f,),
                    )
        elif standard_only:
            with sqlite3.connect(Path.DATABASE) as conn:
                data = conn.cursor().execute(
                    'SELECT "domain" FROM "rules" ORDER BY domain ASC;'
                )
        elif user_only:
            with sqlite3.connect(Path.RULES_DATABASE) as conn:
                data = conn.cursor().execute(
                    'SELECT "domain" FROM "r" ORDER BY domain ASC;'
                )
        else:
            with sqlite3.connect(Path.RULES_DATABASE) as conn:
                data = conn.cursor().execute(
                    'SELECT "domain" FROM "r" ORDER BY domain ASC;'
                )
            with sqlite3.connect(Path.DATABASE) as conn:
                data2 = conn.cursor().execute(
                    'SELECT "domain" FROM "rules" ORDER BY domain ASC;'
                )

        for rule in data:
            output.append(rule[0])
        if data2 is not None:
            for rule in data2:
                output.append(rule[0])
        return output


def list_rules(
    from_filter_lists: list = None,
    user_only: bool = False,
    standard_only: bool = False,
    quiet: bool = False,
) -> None:
    """
    List rules stored in the database

    :param from_filter_lists: List only rules that are set by specified filter lists
    :param user_only: List only user rules
    :param standard_only: List only rules that are set by filter lists (that are not set by the user)
    """
    if from_filter_lists and user_only or user_only and standard_only:
        pass
    elif not os.path.isfile(Path.DATABASE):
        raise FileNotFoundError(
            "database does not exist yet. "
            "Please run 'tblock -Y' with admin privileges to create it"
        )
    else:
        data2 = None
        if from_filter_lists:
            with sqlite3.connect(Path.DATABASE) as conn:
                for f in from_filter_lists:
                    data = conn.cursor().execute(
                        'SELECT "domain", "policy", "ip" FROM "rules" WHERE filter_id=? ORDER BY domain ASC;',
                        (f,),
                    )
        elif standard_only:
            with sqlite3.connect(Path.DATABASE) as conn:
                data = conn.cursor().execute(
                    'SELECT "domain", "policy", "ip" FROM "rules" ORDER BY domain ASC;'
                )
        elif user_only:
            with sqlite3.connect(Path.RULES_DATABASE) as conn:
                data = conn.cursor().execute(
                    'SELECT "domain", "policy", "ip" FROM "r" ORDER BY domain ASC;'
                )
        else:
            with sqlite3.connect(Path.RULES_DATABASE) as conn:
                data = conn.cursor().execute(
                    'SELECT "domain", "policy", "ip" FROM "r" ORDER BY domain ASC;'
                )
            with sqlite3.connect(Path.DATABASE) as conn:
                data2 = conn.cursor().execute(
                    'SELECT "domain", "policy", "ip" FROM "rules" ORDER BY domain ASC;'
                )

        for rule in data:
            if quiet:
                print(rule[0])
            else:
                if rule[1] == RulePolicy.ALLOW:
                    print("ALLOW    " + rule[0])
                elif rule[1] == RulePolicy.BLOCK:
                    print("BLOCK    " + rule[0])
                elif rule[1] == RulePolicy.REDIRECT:
                    print("REDIRECT " + rule[0] + " -> " + rule[2])
        if data2 is not None:
            for rule in data2:
                if quiet:
                    print(rule[0])
                else:
                    if rule[1] == RulePolicy.ALLOW:
                        print("ALLOW    " + rule[0])
                    elif rule[1] == RulePolicy.BLOCK:
                        print("BLOCK    " + rule[0])
                    elif rule[1] == RulePolicy.REDIRECT:
                        print("REDIRECT " + rule[0] + " -> " + rule[2])


def get_rules_count() -> int:
    with sqlite3.connect(Path.DATABASE) as db:
        count = db.cursor().execute("SELECT COUNT() FROM rules;").fetchone()[0]
    with sqlite3.connect(Path.RULES_DATABASE) as db:
        return count + db.cursor().execute("SELECT COUNT() FROM r;").fetchone()[0]

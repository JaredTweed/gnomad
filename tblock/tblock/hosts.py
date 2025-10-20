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
import shutil
import hashlib
import os
import re
import sqlite3

# Local modules
from .config import Path, Var, hosts_are_default
from .style import loading_icon, Icon, Font
from .const import RulePolicy
from .utils import prompt_user, check_root_access
from .exceptions import HostsError


def get_hostname() -> str:
    """Get system hostname
    Returns:
        str: The hostname
    """
    if os.name != "posix" or os.path.isdir("/data/data/com.termux/files/usr/lib/"):
        return ""
    else:
        if os.path.isfile("/etc/hostname"):
            with open("/etc/hostname", "rt") as f:
                for line in f.readlines():
                    if not re.match(r"#", line):
                        return line.split("\n")[0]
        elif os.path.isfile("/etc/conf.d/hostname"):
            with open("/etc/hostname", "rt") as f:
                for line in f.readlines():
                    if not re.match(r"#", line):
                        return line.split("\n")[0].split('hostname="')[1].split('"')[0]
        else:
            return ""


def enable_protection(quiet: bool = False, do_not_prompt: bool = True) -> None:
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    if do_not_prompt or prompt_user(
        "You are about to replace your default hosts file with the one built by TBlock"
    ):
        if not quiet:
            print(f"{Font.BOLD}==> Applying built hosts file")

        if hosts_are_default():
            if os.path.isfile(Path.BUILT_HOSTS_BACKUP):
                if not quiet:
                    print(f" {loading_icon(1)} Checking checksum", end="\r")
                with sqlite3.connect(Path.DATABASE) as conn:
                    s = (
                        conn.cursor()
                        .execute(
                            "SELECT value FROM system WHERE variable='hosts_shasum';",
                        )
                        .fetchone()[0]
                    )
                with open(os.path.join(Path.BUILT_HOSTS_BACKUP), "rb") as f:
                    shasum = hashlib.sha512()
                    for line in f:
                        shasum.update(line)
                if s == shasum.hexdigest():
                    if not quiet:
                        print(f" {Icon.SUCCESS} Checking checksum")
                    __msg = "Saving default hosts file"
                    if not quiet:
                        print(f" {loading_icon(1)} {__msg}", end="\r")
                    shutil.copy(Path.HOSTS, Path.HOSTS_BACKUP)
                    if not quiet:
                        print(f" {Icon.SUCCESS} {__msg}")
                        print(
                            f" {loading_icon(1)} Applying previously built hosts file",
                            end="\r",
                        )
                    shutil.copy(Path.BUILT_HOSTS_BACKUP, Path.HOSTS)
                    os.remove(Path.BUILT_HOSTS_BACKUP)
                    if not quiet:
                        print(f" {Icon.SUCCESS} Applying previously built hosts file")
                        print(f" {Icon.INFORMATION} " + "Protection is now enabled")
                else:
                    if not quiet:
                        print(f" {Icon.ERROR} Checking checksum")
                        print(
                            f" {Icon.INFORMATION} Run tblock -B to build the hosts file"
                        )
                        raise SystemExit(1)
            elif not quiet:
                print(f" {Icon.WARNING} TBlock has never built the hosts file")
                print(f" {Icon.INFORMATION} Run tblock -B to build the hosts file")
        elif not quiet:
            print(f" {Icon.WARNING} Protection is already active")
            print(f" {Icon.INFORMATION} Run tblock -B to rebuild the hosts file")


def update_hosts(quiet: bool = False, do_not_prompt: bool = True) -> None:
    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    if do_not_prompt or prompt_user("You are about to build a whole new hosts file"):
        if not quiet:
            print(f"{Font.BOLD}==> Building hosts file")

        # Backup hosts if tblock is not yet active
        if hosts_are_default():
            enabling_protection = True
            __msg = "Saving default hosts file"
            if not quiet:
                print(f" {loading_icon(1)} {__msg}", end="\r")
            with open(Path.HOSTS, "rt") as f:
                default_hosts = f.read()
            with open(Path.HOSTS_BACKUP, "wt") as w:
                w.write(default_hosts)
            if not quiet:
                print(f" {Icon.SUCCESS} {__msg}")
        else:
            enabling_protection = False
            with open(Path.HOSTS_BACKUP, "rt") as f:
                default_hosts = f.read()

        # Update temporary file to avoid causing damage to hosts
        with open(os.path.join(Path.TMP_DIR, "hosts.txt"), "wt") as w:
            db = sqlite3.connect(Path.RULES_DATABASE)
            cursor = db.cursor()
            total_rules = cursor.execute("SELECT COUNT() FROM r;").fetchone()[0]
            rules = cursor.execute(
                "SELECT domain, policy, ip FROM r WHERE policy != ? ORDER BY domain ASC;",
                (RulePolicy.ALLOW,),
            )

            db2 = sqlite3.connect(Path.DATABASE)
            cursor2 = db2.cursor()
            total_rules2 = cursor2.execute("SELECT COUNT() FROM rules;").fetchone()[0]
            rules2 = cursor2.execute(
                "SELECT domain, policy, ip FROM rules WHERE policy != ? ORDER BY domain ASC;",
                (RulePolicy.ALLOW,),
            )
            count = 0
            invalid = False
            w.write(
                f"# This file is generated by TBlock\n"
                f"# Do not edit it manually, otherwise your changes will be overwritten"
                f"\n\n# ----- DEFAULT HOSTS -----\n{default_hosts}\n\n# ----- CUSTOM RULES -----\n"
            )
        with open(os.path.join(Path.TMP_DIR, "hosts.txt"), "at") as w:
            content = ""
            __msg = "Processing user rules:"
            if not quiet:
                print(
                    f" {loading_icon(count)} {__msg} {count}/{total_rules} (0%)",
                    end="\r",
                )
            for row in rules:
                count += 1
                if not invalid:
                    if row[1] == RulePolicy.BLOCK:
                        content += f"{Var.DEFAULT_IP}\t\t{row[0]}\n"
                        if Var.ALLOW_IPV6:
                            content += f"{Var.DEFAULT_IPV6}\t\t\t{row[0]}\n"
                    elif row[1] == RulePolicy.REDIRECT:
                        content += f"{row[2]}\t\t{row[0]}\n"
                if count % 100000 == 0:
                    percent = int(count * 100 / total_rules)
                    if not quiet:
                        print(
                            f" {loading_icon(count / 100000)} {__msg} {count}/{total_rules} ({percent}%)",
                            end="\r",
                        )
                    w.write(content)
                    content = ""
            if not quiet:
                print(f" {Icon.SUCCESS} {__msg} {total_rules}/{total_rules} (100%)")
            content += "\n\n# ----- TBLOCK RULES -----\n"
            db.close()
            w.write(content)
            content = ""
            __msg = "Processing rules:"
            if not quiet:
                print(
                    f" {loading_icon(count)} {__msg} {count}/{total_rules2} (0%)",
                    end="\r",
                )
            for row in rules2:
                count += 1
                if not invalid:
                    if row[1] == RulePolicy.BLOCK:
                        content += f"{Var.DEFAULT_IP}\t\t{row[0]}\n"
                        if Var.ALLOW_IPV6:
                            content += f"{Var.DEFAULT_IPV6}\t\t\t{row[0]}\n"
                    elif row[1] == RulePolicy.REDIRECT:
                        content += f"{row[2]}\t\t{row[0]}\n"
                if count % 100000 == 0:
                    percent = int(count * 100 / total_rules2)
                    if not quiet:
                        print(
                            f" {loading_icon(count / 100000)} {__msg} {count}/{total_rules2} ({percent}%)",
                            end="\r",
                        )
                    w.write(content)
                    content = ""
            db2.close()
            w.write(content)
        if not quiet:
            print(f" {Icon.SUCCESS} {__msg} {total_rules2}/{total_rules2} (100%)")

        # Write changes into hosts file
        __msg = "Writing new hosts file"
        if not quiet:
            print(f" {loading_icon(1)} {__msg}", end="\r")
        with open(os.path.join(Path.TMP_DIR, "hosts.txt"), "rb") as f:
            shasum = hashlib.sha512()
            for line in f:
                shasum.update(line)
        with sqlite3.connect(Path.DATABASE) as conn:
            conn.cursor().execute(
                "UPDATE system SET value=? WHERE variable='hosts_shasum';",
                (shasum.hexdigest(),),
            )
        shutil.copy(os.path.join(Path.TMP_DIR, "hosts.txt"), Path.HOSTS)
        if not quiet:
            print(f" {Icon.SUCCESS} {__msg}")
        if not quiet and enabling_protection:
            print(f" {Icon.INFORMATION} " + "Protection is now enabled")


def restore_hosts(quiet: bool = False, do_not_prompt: bool = True) -> None:
    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    if not hosts_are_default():
        if do_not_prompt or prompt_user("You are about to update your hosts file"):
            __msg = "Restoring stock hosts file"
            if not quiet:
                print(f"{Font.BOLD}==> {__msg}")
                print(
                    f" {loading_icon(1)} Backing up previously built hosts file",
                    end="\r",
                )
            shutil.copy(Path.HOSTS, Path.BUILT_HOSTS_BACKUP)
            if not quiet:
                print(f" {Icon.SUCCESS} Backing up previously built hosts file")
                print(f" {loading_icon(1)} {__msg}", end="\r")
            shutil.copy(Path.HOSTS_BACKUP, Path.HOSTS)
            os.remove(Path.HOSTS_BACKUP)
            if not quiet:
                print(f" {Icon.SUCCESS} {__msg}")
                print(f" {Icon.WARNING} " + "Protection is now disabled")
    else:
        raise HostsError("default hosts file already restored")


def remove_from_hosts(domains: dict, quiet: bool = False) -> None:
    if not quiet:
        print(f"{Font.BOLD}==> Updating hosts file")
    if not hosts_are_default():
        count = 0
        with open(Path.HOSTS, "rt") as f:
            new_hosts = f.read()
        for _d in domains.keys():
            if "*" not in list(_d):
                count += 1
                if not quiet:
                    print(
                        f" {loading_icon(count)} Applying new rules to hosts file",
                        end="\r",
                    )
                if domains[_d] is not None:
                    new_hosts = new_hosts.replace(f"{domains[_d]}\t\t{_d}\n", "")
                else:
                    new_hosts = new_hosts.replace(f"{Var.DEFAULT_IP}\t\t{_d}\n", "")
                    if Var.ALLOW_IPV6:
                        new_hosts = new_hosts.replace(
                            f"{Var.DEFAULT_IPV6}\t\t\t{_d}\n", ""
                        )
        with open(os.path.join(Path.TMP_DIR, "hosts.txt"), "wt") as f:
            f.write(new_hosts)
        with open(os.path.join(os.path.join(Path.TMP_DIR, "hosts.txt")), "rt") as f:
            content = f.read()
            shasum = hashlib.sha512(content.encode("utf-8")).hexdigest()
        with sqlite3.connect(Path.DATABASE) as conn:
            conn.cursor().execute(
                "UPDATE system SET value=? WHERE variable='hosts_shasum';", (shasum,)
            )
        with open(Path.HOSTS, "wt") as f:
            f.write(new_hosts)
        if not quiet:
            print(f" {Icon.SUCCESS} Applying new rules to hosts file")
    elif not quiet:
        print(f" {Icon.ERROR} Applying new rules to hosts file")
        print(f" {Icon.WARNING} TBlock is not active")


def add_to_hosts(domains: list, ip: str = None, quiet: bool = False) -> None:
    if not quiet:
        print(f"{Font.BOLD}==> Updating hosts file")
    if not hosts_are_default():
        count = 0
        content = ""
        for _d in domains:
            count += 1
            if not quiet:
                print(
                    f" {loading_icon(count)} Applying new rules to hosts file", end="\r"
                )
            if ip:
                content += f"{ip}\t\t{_d}\n"
            else:
                content += f"{Var.DEFAULT_IP}\t\t{_d}\n"
                if Var.ALLOW_IPV6:
                    content += f"{Var.DEFAULT_IPV6}\t\t\t{_d}\n"
        with open(os.path.join(Path.TMP_DIR, "hosts.txt"), "at") as f:
            f.write(content)
        with open(os.path.join(Path.TMP_DIR, "hosts.txt"), "rb") as f:
            c = f.read()
            shasum = hashlib.sha512(c).hexdigest()
        with sqlite3.connect(Path.DATABASE) as conn:
            conn.cursor().execute(
                "UPDATE system SET value=? WHERE variable='hosts_shasum';", (shasum,)
            )
        with open(Path.HOSTS, "at") as f:
            f.write(content)
        if not quiet:
            print(f" {Icon.SUCCESS} Applying new rules to hosts file")
    elif not quiet:
        print(f" {Icon.ERROR} Applying new rules to hosts file")
        print(f" {Icon.WARNING} TBlock is not active")


def gen_hosts() -> None:
    hostname = get_hostname()
    print(
        "127.0.0.1    localhost\n"
        "::1          localhost    ip6-localhost    ip6-loopback\n"
        "ff02::1      ip6-allnodes\n"
        "ff02::2      ip6-allrouters"
    )
    if hostname:
        print(f"127.0.1.1    {hostname}    {hostname}.localdomain")

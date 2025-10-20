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
import hashlib
import os.path
import datetime
import configparser
import sqlite3


VERSION = "2.7.5"
REPO_COMPATIBLE_VERSION = "2.4.0"


class Path:
    TERMUX_ROOT = "/data/data/com.termux/files/usr/"

    # The script is running on Termux
    if os.path.isdir(TERMUX_ROOT):
        PREFIX = os.path.join(TERMUX_ROOT, "lib", "tblock")
        HOSTS = os.path.join("/", "system", "etc", "hosts")
        TMP_DIR = os.path.join(TERMUX_ROOT, "tmp", "tblock")
        CONFIG = os.path.join(TERMUX_ROOT, "etc", "tblock.conf")
        LOGS = os.path.join(TERMUX_ROOT, "var", "log", "tblock.log")
        CACHE = os.path.join(TERMUX_ROOT, "var", "cache", "tblock")
        DAEMON_PID = os.path.join(TERMUX_ROOT, "var", "run", "tblockd.pid")

    # The script is running on POSIX
    elif os.name == "posix":
        PREFIX = os.path.join("/", "var", "lib", "tblock")
        HOSTS = os.path.join("/", "etc", "hosts")
        TMP_DIR = os.path.join("/", "tmp", "tblock")
        CONFIG = os.path.join("/", "etc", "tblock.conf")
        LOGS = os.path.join("/", "var", "log", "tblock.log")
        CACHE = os.path.join("/", "var", "cache", "tblock")
        DAEMON_PID = os.path.join("/", "run", "tblockd.pid")

    # The script is running on Windows
    elif os.name == "nt":
        PREFIX = os.path.join(os.path.expandvars("%ALLUSERSPROFILE%"), "TBlock")
        HOSTS = os.path.join(
            os.path.expandvars("%WINDIR%"), "System32", "drivers", "etc", "hosts"
        )
        TMP_DIR = os.path.join(os.path.expandvars("%TMP%"), "tblock")
        CONFIG = os.path.join(PREFIX, "conf.ini")
        LOGS = os.path.join(PREFIX, "log", "tblock.log")
        CACHE = os.path.join(PREFIX, "cache")
        DAEMON_PID = os.path.join(PREFIX, "_tblock.pid")

    # If the script is running on an unsupported platform, raise an error
    else:
        raise OSError("TBlock is currently not supported on your operating system")

    # Define other paths
    DATABASE = os.path.join(PREFIX, "storage.sqlite")
    RULES_DATABASE = os.path.join(PREFIX, "user.db")
    HOSTS_BACKUP = os.path.join(PREFIX, "hosts.bak")
    DB_LOCK = os.path.join(PREFIX, ".db_lock")
    BUILT_HOSTS_BACKUP = os.path.join(PREFIX, "active.hosts.bak")


def load_config(config_file: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(config_file)
    return config


class Var:
    __config = load_config(Path.CONFIG)

    try:
        DEFAULT_IP = __config.get("hosts", "default_ip")
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        DEFAULT_IP = "0.0.0.0"
    try:
        DEFAULT_IPV6 = __config.get("hosts", "default_ipv6")
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        DEFAULT_IPV6 = "::1"
    try:
        ALLOW_IPV6 = __config.getboolean("hosts", "allow_ipv6")
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        ALLOW_IPV6 = False

    REPO_MIRRORS = [
        "https://update.tblock.me/2.4.0/index.json",
        "https://tblock.codeberg.page/repo/2.4.0/index.json",
        "https://codeberg.org/tblock/repo/raw/branch/pages/2.4.0/index.json",
    ]


def hosts_are_safe() -> bool:
    """
    Check if the hosts file's saved sha512sum is the same as the active hosts file's sha512sum.
    This can be useful to prevent hosts hijack
    """
    with open(Path.HOSTS, "rb") as f:
        hosts_shasum = hashlib.sha512(f.read()).hexdigest()
    with sqlite3.connect(Path.DATABASE) as conn:
        hosts_backup_shasum = (
            conn.cursor()
            .execute("SELECT value FROM system WHERE variable='hosts_shasum';")
            .fetchone()[0]
        )
    return bool(hosts_shasum == hosts_backup_shasum)


def hosts_are_default() -> bool:
    """
    Check if the default hosts file have been restored
    """
    if os.path.isfile(Path.HOSTS_BACKUP):
        return False
    else:
        return True


def log_message(message: str) -> None:
    """Write a message in TBlock's log file

    :param message: The message to log
    """
    try:
        with open(Path.LOGS, "at") as logging:
            logging.write(f'{datetime.datetime.now().strftime("%D %r")} {message}\n')
    except (PermissionError, FileNotFoundError):
        pass


def create_dirs() -> None:
    """
    Create the directories required by TBlock
    """
    for x in [Path.PREFIX, Path.CACHE, os.path.dirname(Path.LOGS), Path.TMP_DIR]:
        if not os.path.isdir(x):
            try:
                os.makedirs(x, exist_ok=True)
            except PermissionError:
                pass

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
import os
import sqlite3

# External modules
from colorama import Fore, Style, init

# Local modules
from .config import VERSION, Path, hosts_are_safe, hosts_are_default


# Compatibility with Windows
# See: https://codeberg.org/tblock/tblock/pulls/17
if os.name == "nt":
    # On POSIX, this breaks the colors
    init(convert=True)


class Icon:
    SUCCESS = f"{Fore.GREEN}[\u2713]{Style.RESET_ALL}"
    INFORMATION = f"{Fore.BLUE}[i]{Style.RESET_ALL}"
    WARNING = f"{Fore.YELLOW}[!]{Style.RESET_ALL}"
    ERROR = f"{Fore.RED}[x]{Style.RESET_ALL}"
    LOADING_1 = f"{Fore.WHITE}[-]{Style.RESET_ALL}"
    LOADING_2 = f"{Fore.WHITE}[\\]{Style.RESET_ALL}"
    LOADING_3 = f"{Fore.WHITE}[|]{Style.RESET_ALL}"
    LOADING_4 = f"{Fore.WHITE}[/]{Style.RESET_ALL}"


class Font:
    BOLD = "\033[1m"
    DEFAULT = "\033[0m"
    UNDERLINE = "\033[4m"


def loading_icon(number: int) -> str:
    if number % 4 == 0 and number % 3 != 0:
        return Icon.LOADING_4
    elif number % 2 == 0 and number % 3 != 0:
        return Icon.LOADING_2
    elif number % 3 == 0:
        return Icon.LOADING_3
    else:
        return Icon.LOADING_1


# These functions are only used to display the status page


def status_tblock_enabled(quiet: bool = False) -> str:
    if not hosts_are_default():
        return Fore.GREEN + "active" if not quiet else "active"
    else:
        return Fore.RED + "inactive" if not quiet else "inactive"


def status_get_platform() -> str:
    if os.path.isdir(Path.TERMUX_ROOT):
        return "android"
    elif os.name == "nt":
        return "windows"
    elif os.path.isdir("/Users/"):
        return "mac"
    elif os.name == "posix":
        return "linux"
    else:
        return "-"


def status_hosts_hijack(quiet: bool = False) -> str:
    if hosts_are_safe():
        return Fore.GREEN + "undetected" if not quiet else "undetected"
    elif hosts_are_default():
        return Fore.RED + "tblock is inactive" if not quiet else "tblock is inactive"
    else:
        return Fore.RED + "detected" if not quiet else "detected"


def status_daemon_running(quiet: bool = False) -> str:
    if os.path.isfile(Path.DAEMON_PID):
        return Fore.GREEN + "running" if not quiet else "running"
    else:
        return Fore.RED + "not running" if not quiet else "not running"


def repo_version() -> int:
    with sqlite3.connect(Path.DATABASE) as db:
        cursor = db.cursor()
        try:
            return int(
                cursor.execute(
                    'SELECT value FROM system WHERE variable="repo_version";'
                ).fetchone()[0]
            )
        except (IndexError, TypeError):
            return 0


def show_status(quiet: bool = False) -> None:
    if not os.path.isfile(Path.DATABASE):
        raise FileNotFoundError(
            "database does not exist yet. "
            "Please run 'tblock -Y' with admin privileges to create it"
        )
    with sqlite3.connect(Path.DATABASE) as db:
        total_rules = (
            db.cursor()
            .execute(
                "SELECT SUM(rules_count) FROM filters "
                "WHERE rules_count IS NOT NULL and rules_count!=0 AND subscribing=1;"
            )
            .fetchone()[0]
        )
        total_filter_lists = (
            db.cursor()
            .execute("SELECT COUNT(id) FROM filters WHERE subscribing=1;")
            .fetchone()[0]
        )
    if not quiet:
        print(
            f"{Font.BOLD}{Fore.LIGHTMAGENTA_EX}\n"
            f"       xxxxxxxxxxxx          TBlock v{VERSION}\n"
            f"    xxxxxxxxxxxxxxxxxx       {Font.DEFAULT}{Fore.RESET}-------------{Font.BOLD}{Fore.LIGHTMAGENTA_EX}\n"
            f"  xxxxx{Fore.RESET}ooooooooooo{Fore.LIGHTMAGENTA_EX}xxxxx      "
            f"Protection: {Fore.GREEN}{status_tblock_enabled()}{Fore.LIGHTMAGENTA_EX}\n"
            f"  xxxxxxxxxx{Fore.RESET}oo{Fore.LIGHTMAGENTA_EX}xxxxxxxxxx     "
            f"Platform: {Fore.YELLOW}{status_get_platform()}{Fore.LIGHTMAGENTA_EX}\n"
            f" xxxxxxxxxxx{Fore.RESET}oo{Fore.LIGHTMAGENTA_EX}xxxxxxxxxxx    "
            f"Daemon: {Fore.GREEN}{status_daemon_running()}{Fore.LIGHTMAGENTA_EX}\n"
            f"  xxxxxxxxxx{Fore.RESET}oo{Fore.LIGHTMAGENTA_EX}xxxxxxxxxx     "
            f"Rules: {Fore.LIGHTBLUE_EX}{total_rules}{Fore.LIGHTMAGENTA_EX}\n"
            f"  xxxxxxxxxx{Fore.RESET}oo{Fore.LIGHTMAGENTA_EX}xxxxxxxxxx     "
            f"Filter lists: {Fore.LIGHTBLUE_EX}{total_filter_lists}{Fore.LIGHTMAGENTA_EX}\n"
            f"    xxxxxxxx{Fore.RESET}oo{Fore.LIGHTMAGENTA_EX}xxxxxxxx       "
            f"Repository: {Fore.YELLOW}v{repo_version()}{Fore.LIGHTMAGENTA_EX}\n"
            f"       xxxxxxxxxxxx          "
            f"Hosts hijack: {Fore.GREEN}{status_hosts_hijack()}{Font.DEFAULT}{Fore.RESET}\n"
            f"\n"
        )
    else:
        print(
            f"TBlock v{VERSION}\n"
            f"Protection: {status_tblock_enabled(quiet)}\n"
            f"Platform: {status_get_platform()}\n"
            f"Daemon: {status_daemon_running(quiet)}\n"
            f"Rules: {total_rules}\n"
            f"Filter lists: {total_filter_lists}\n"
            f"Repository: {repo_version()}\n"
            f"Hosts hijack: {status_hosts_hijack(quiet)}"
        )

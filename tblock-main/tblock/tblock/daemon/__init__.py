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
import time
import signal
import configparser
import datetime

# Local modules
from tblock.filters import Filter, get_all_filter_lists, sync_filter_list_repo
from tblock.config import (
    load_config,
    log_message,
    Path,
)
from tblock.style import Font
from tblock.utils import check_root_access, unlock_db, lock_db
from tblock.exceptions import RepoError, FilterError, TBlockError, DatabaseLockedError


class SignalHandler:
    """
    Handler for SIGTERM and SIGINT
    """

    stopped = False
    signame = None

    def __init__(self):
        signal.signal(signal.SIGINT, self.sigint)
        signal.signal(signal.SIGTERM, self.sigterm)

    def sigint(self, *args):
        self.stopped = True
        self.signame = "SIGINT"

    def sigterm(self, *args):
        self.stopped = True
        self.signame = "SIGTERM"


def start_daemon(config: str, no_pid: bool = False, quiet: bool = False) -> None:
    """
    Start the daemon

    :param config: Path to the config file to use
    :param no_pid: Optional. Do not create a PID file (False by default)
    :param quiet: Optional. Do not print any output (False by default)
    """
    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")
    if not os.path.isfile(config):
        raise FileNotFoundError("config file not found: {0}".format(config))
    try:
        daemon_config = load_config(config)
    except KeyError:
        raise TBlockError("invalid config file: {0}".format(config))
    if os.path.isfile(Path.DAEMON_PID) and not no_pid:
        with open(Path.DAEMON_PID, "rt") as f:
            if not int(f.read()) == os.getpid():
                log_message(
                    "[tblockd] ERROR: an instance of the daemon is already running"
                )
                raise TBlockError(
                    "an instance of the daemon is already running. Try to run with the --no-pid option"
                )
    else:
        if not no_pid:
            with open(Path.DAEMON_PID, "wt") as w:
                w.write(str(os.getpid()))
        try:
            frequency = daemon_config.getint("daemon", "frequency")
            # Prevent the frequency from being set to a value lower than 12 hour
            if frequency < 12:
                frequency = 12
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            frequency = 48
        try:
            sync_repo = daemon_config.getboolean("daemon", "sync_repo")
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            sync_repo = True
        try:
            force = daemon_config.getboolean("daemon", "force")
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            force = False

        with sqlite3.connect(Path.DATABASE) as conn:
            cur = conn.cursor()
            last_update = cur.execute(
                "SELECT value FROM system WHERE variable=?;", ("daemon_update",)
            ).fetchone()
            if last_update:
                last_update = int(last_update[0])
            else:
                last_update = None

        log_message(
            "[tblockd] INFO:  config loaded; PID: {0}; launching updater now".format(
                os.getpid()
            )
        )
        updater(
            sync_repo=sync_repo,
            frequency=frequency,
            do_not_remove_pid=no_pid,
            force=force,
            quiet=quiet,
            last_update=last_update,
        )


def time_left(last_update: int, frequency: int) -> int:
    # This has to be redesigned to use datetime directly
    # But it seems to work though
    # TODO: change this shit
    if last_update and last_update + frequency > int(
        datetime.datetime.now().strftime("%Y%m%d%H")
    ):
        return (last_update + frequency) - int(
            datetime.datetime.now().strftime("%Y%m%d%H")
        )
    else:
        return 0


def save_update_time():
    with sqlite3.connect(Path.DATABASE) as conn:
        cur = conn.cursor()
        last_update = cur.execute(
            "SELECT value FROM system WHERE variable=?;", ("daemon_update",)
        ).fetchone()
        if last_update:
            cur.execute(
                "UPDATE system SET value=? WHERE variable=?;",
                (int(datetime.datetime.now().strftime("%Y%m%d%H")), "daemon_update"),
            )
        else:
            cur.execute(
                "INSERT INTO system (value, variable) VALUES (?, ?);",
                (int(datetime.datetime.now().strftime("%Y%m%d%H")), "daemon_update"),
            )


def updater(
    sync_repo: bool = False,
    frequency: int = 12,
    do_not_remove_pid: bool = False,
    last_update: int = 0,
    force: bool = False,
    quiet: bool = False,
) -> None:
    process = SignalHandler()
    while not process.stopped:
        hours_left = time_left(last_update=last_update, frequency=frequency)
        if hours_left:
            if not quiet:
                print(
                    f"{Font.BOLD}==> Update was already done, waiting {hours_left} hour(s)...{Font.DEFAULT}"
                )
            x = 1
            while hours_left:
                hours_left = time_left(last_update=last_update, frequency=frequency)
                if process.stopped:
                    break
                time.sleep(1)
                x += 1

        if process.stopped:
            if not do_not_remove_pid:
                os.remove(Path.DAEMON_PID)
            log_message(
                "[tblockd] INFO:  caught {0}; PID: {1}; stopping now".format(
                    process.signame, os.getpid()
                )
            )
            break

        try:
            # Lock the database
            lock_db()
        except DatabaseLockedError:
            # Wait one second before trying again and check for hosts hijack if enabled
            if process.stopped:
                break
            if not quiet:
                print(
                    f"{Font.BOLD}==> Database locked, waiting for other instances to terminate{Font.DEFAULT}",
                    end="\r",
                )
            time.sleep(1)
            continue

        if process.stopped:
            break

        log_message(
            "[tblockd] INFO:  PID: {0}; updating filter lists now".format(os.getpid())
        )
        if sync_repo:
            try:
                sync_filter_list_repo(quiet=quiet, force=force, lock_database=False)
            except RepoError:
                pass
        for i in get_all_filter_lists(subscribing_only=True):
            if process.stopped:
                break
            f = Filter(i, quiet=quiet)
            if not quiet:
                print(f"{Font.BOLD}==> Updating filter list: {f.id}{Font.DEFAULT}")
            try:
                f.retrieve()
                if process.stopped:
                    break
                f.update(force=force)
            except FilterError:
                pass
            except FileNotFoundError as err:
                log_message(
                    "[tblockd] ERROR:  PID: {0}; caught FileNotFoundError: {1}".format(
                        os.getpid(), err.__str__()
                    )
                )
            del f

        save_update_time()

        # Unlock the database
        unlock_db()

        log_message(
            "[tblockd] INFO:  PID: {0}; operation was successful".format(os.getpid())
        )
        if not quiet:
            print(
                f"{Font.BOLD}==> Waiting {frequency} hour(s) until next update...{Font.DEFAULT}"
            )
        x = 1
        while x <= frequency * 3600:
            if process.stopped:
                break
            time.sleep(1)
            x += 1
    else:
        if not do_not_remove_pid:
            os.remove(Path.DAEMON_PID)
        log_message(
            "[tblockd] INFO:  caught {0}; PID: {1}; stopping now".format(
                process.signame, os.getpid()
            )
        )

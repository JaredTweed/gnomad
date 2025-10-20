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
import os.path
import sqlite3
import hashlib

# Local modules
from .config import Path, VERSION, log_message
from .style import Font
from .const import RulePolicy, USER_RULE_PRIORITY


def setup_new_database(quiet: bool = False) -> None:
    """
    Create a new database, compatible with the latest version of TBlock

    :param quiet: Optional. Do not display an output (false by default)
    """
    if not quiet:
        print(f"{Font.BOLD}==> Creating new database{Font.DEFAULT}")
        log_message(
            f"[core]    INFO:  creating new sqlite database under: {Path.DATABASE}"
        )
    with sqlite3.connect(Path.DATABASE) as conn:
        conn.cursor().execute(
            """CREATE TABLE IF NOT EXISTS "filters" (
            "id"	TEXT NOT NULL UNIQUE,
            "source"	TEXT NOT NULL UNIQUE,
            "mirrors"	TEXT,
            "metadata"	TEXT,
            "on_repo"	INTEGER,
            "permissions"	TEXT,
            "subscribing"	INTEGER NOT NULL,
            "syntax"	TEXT,
            "rules_count"   INTEGER,
            PRIMARY KEY("id")
        );"""
        )
        conn.cursor().execute(
            """CREATE TABLE IF NOT EXISTS "rules" (
            "domain"	TEXT NOT NULL UNIQUE,
            "policy"	TEXT NOT NULL,
            "filter_id"	TEXT NOT NULL,
            "ip"	TEXT,
            PRIMARY KEY("domain")
        );"""
        )
        conn.cursor().execute(
            """CREATE TABLE IF NOT EXISTS "system" (
            "variable"  TEXT NOT NULL UNIQUE,
            "value" BLOB NOT NULL
        );"""
        )
        conn.cursor().execute(
            """CREATE TABLE IF NOT EXISTS "cache" (
            "key"  TEXT NOT NULL UNIQUE,
            "sha512" TEXT NOT NULL
        );"""
        )
        try:
            conn.cursor().execute(
                'INSERT INTO system (variable, value) VALUES ("db_version", ?);',
                (VERSION,),
            )
            conn.cursor().execute(
                'INSERT INTO system (variable, value) VALUES ("hosts_shasum", ?);',
                ("",),
            )
        except sqlite3.IntegrityError:
            pass
        conn.commit()
    with sqlite3.connect(Path.RULES_DATABASE) as conn:
        conn.cursor().execute(
            """CREATE TABLE IF NOT EXISTS "r" (
            "domain"    TEXT NOT NULL UNIQUE,
            "policy"    TEXT NOT NULL,
            "ip"    TEXT,
            PRIMARY KEY("domain")
        );"""
        )


def update_database_from_2_4_1(quiet: bool = False) -> None:
    """
    :param quiet: Optional. Do not display an output (false by default)
    """
    with sqlite3.connect(Path.DATABASE) as conn:
        user_rules = conn.cursor().execute(
            "SELECT domain, policy, ip FROM rules WHERE filter_id=?",
            (USER_RULE_PRIORITY,),
        )
        print(f"{Font.BOLD}==> Moving user rules to second database{Font.DEFAULT}")
        with sqlite3.connect(Path.RULES_DATABASE) as conn2:
            cur = conn2.cursor()
            for x in user_rules:
                cur.execute(
                    "INSERT INTO r (domain, policy, ip) VALUES (?, ?, ?)",
                    (x[0], x[1], x[2]),
                )
        conn.cursor().execute(
            "DELETE FROM rules WHERE filter_id=?", (USER_RULE_PRIORITY,)
        )


def update_database_from_2_6_1(quiet: bool = False) -> None:
    """
    :param quiet: Optional. Do not display an output (false by default)
    """
    with sqlite3.connect(Path.DATABASE) as conn:
        conn.cursor().execute("ALTER TABLE filters DROP COLUMN permissions;")


def update_database_from_2_7_1(quiet: bool = False) -> None:
    """
    :param quiet: Optional. Do not display an output (false by default)
    """
    with sqlite3.connect(Path.DATABASE) as conn:
        conn.cursor().execute(
            "DELETE FROM rules WHERE domain IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
            (
                "0.0.0.0",
                "localhost",
                "localhost.localdomain",
                "local",
                "broadcasthost",
                "ip6-localhost",
                "ip6-loopback",
                "ip6-localnet",
                "ip6-mcastprefix",
                "ip6-allnodes",
                "ip6-allrouters",
                "ip6-allhosts",
            ),
        )


def update_database_from_2_3_0(quiet: bool = False) -> None:
    """
    :param quiet: Optional. Do not display an output (false by default)
    """
    with sqlite3.connect(Path.DATABASE) as conn:
        conn.cursor().execute(
            "UPDATE filters SET syntax=? WHERE syntax=?", ("tblock_legacy", "tblock")
        )


def update_database_from_1_3_2(quiet: bool = False) -> None:
    """
    :param quiet: Optional. Do not display an output (false by default)
    """
    if not quiet:
        print(
            f"{Font.BOLD}==> Updating database from v1.3.2 to v{VERSION}{Font.DEFAULT}"
        )
    log_message(
        f"[core]    INFO:  updating sqlite database from v1.3.2 to v{VERSION} under: {Path.DATABASE}"
    )

    # Handle files used by v1.3.2
    if os.path.isfile(os.path.join(Path.PREFIX, "hosts")):
        os.rename(os.path.join(Path.PREFIX, "hosts"), Path.HOSTS_BACKUP)
    if os.path.isfile(os.path.join(Path.PREFIX, ".needs-update")):
        os.remove(os.path.join(Path.PREFIX, ".needs-update"))
    if os.path.isfile(os.path.join(Path.PREFIX, ".db-lock")):
        os.rename(os.path.join(Path.PREFIX, ".db-lock"), Path.DB_LOCK)

    with sqlite3.connect(Path.DATABASE) as conn:
        # Remove the column "priority"
        # Since the following isn't supported in SQLite3:
        # cursor.execute('ALTER TABLE rules DROP COLUMN "priority";')
        cursor = conn.cursor()
        cursor.execute("CREATE TEMPORARY TABLE rules_backup(d,p,f,i);")
        cursor.execute(
            "INSERT INTO rules_backup SELECT domain,policy,filter_id,ip FROM rules;"
        )
        cursor.execute("DROP TABLE rules;")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS "rules" (
            "domain"	TEXT NOT NULL UNIQUE,
            "policy"	TEXT NOT NULL,
            "filter_id"	TEXT NOT NULL,
            "ip"	TEXT,
            PRIMARY KEY("domain")
        );"""
        )
        cursor.execute("INSERT INTO rules SELECT d,p,f,i FROM rules_backup;")
        cursor.execute("DROP TABLE rules_backup;")

        # Update the database
        cursor.execute('ALTER TABLE filters ADD COLUMN "syntax"    TEXT;')
        cursor.execute('ALTER TABLE filters ADD COLUMN "rules_count"   INTEGER;')
        cursor.execute('ALTER TABLE filters RENAME COLUMN "on_rfr" TO "on_repo";')
        cursor.execute(
            "UPDATE rules SET policy=? WHERE policy=?", (RulePolicy.ALLOW, "allow")
        )
        cursor.execute(
            "UPDATE rules SET policy=? WHERE policy=?", (RulePolicy.BLOCK, "block")
        )
        cursor.execute(
            "UPDATE rules SET policy=? WHERE policy=?",
            (RulePolicy.REDIRECT, "redirect"),
        )
    conn.commit()
    setup_new_database(quiet=True)

    # Post-upgrade transactions
    if os.path.isfile(os.path.join(Path.PREFIX, "repo")):
        with open(os.path.join(Path.PREFIX, "repo"), "rt") as r:
            conn.cursor().execute(
                'INSERT INTO system (variable, value) VALUES ("repo_version", ?);',
                (int(r.read()),),
            )
        os.remove(os.path.join(Path.PREFIX, "repo"))
    if os.path.isfile(os.path.join(Path.PREFIX, "hosts_protection")):
        with open(Path.HOSTS, "rb") as f:
            hosts_shasum = hashlib.sha512(f.read()).hexdigest()
        with open(os.path.join(Path.PREFIX, "hosts_protection"), "rb") as f:
            hosts_backup_shasum = hashlib.sha512(f.read()).hexdigest()
        if hosts_shasum == hosts_backup_shasum:
            conn.cursor().execute(
                'UPDATE system SET value=? WHERE variable="hosts_shasum";',
                (hosts_shasum,),
            )
        os.remove(os.path.join(Path.PREFIX, "hosts_protection"))
    conn.commit()


def update_database_from_1_2_0(quiet: bool = False) -> None:
    """
    :param quiet: Optional. Do not display an output (false by default)
    """
    if not quiet:
        print(
            f"{Font.BOLD}==> Updating database from v1.2.0 to v{VERSION}{Font.DEFAULT}"
        )
        log_message(
            f"[core]    INFO:  updating sqlite database from v1.2.0 to v{VERSION} under: {Path.DATABASE}"
        )
    with sqlite3.connect(Path.DATABASE) as conn:
        conn.cursor().execute('ALTER TABLE "filters" ADD COLUMN "mirrors";')
        conn.commit()
    update_database_from_1_3_2(quiet=True)


def init_db(quiet: bool = False) -> None:
    """
    Update or create a new database if the current does not exist/is not up-to-date

    :param quiet: Optional. Do not display an output (false by default)
    """
    if not os.path.isfile(Path.DATABASE):
        setup_new_database(quiet=quiet)
    else:
        try:
            with sqlite3.connect(Path.DATABASE) as conn:
                conn.cursor().execute("SELECT mirrors FROM filters;")
        except sqlite3.OperationalError:
            update_database_from_1_2_0(quiet=quiet)
        else:
            try:
                with sqlite3.connect(Path.DATABASE) as conn:
                    conn.cursor().execute("SELECT priority FROM rules;")
            except sqlite3.OperationalError:
                try:
                    conn = sqlite3.connect(Path.DATABASE)
                    db_version = (
                        conn.cursor()
                        .execute(
                            'SELECT value FROM system WHERE variable="db_version";'
                        )
                        .fetchone()[0]
                    )
                except sqlite3.OperationalError:
                    log_message(
                        f"[core]    INFO:  an unknown error occurred while upgrading the database to version {VERSION}"
                    )
                else:
                    if db_version < VERSION:
                        print(
                            f"{Font.BOLD}==> Updating database from v{db_version} to v{VERSION}{Font.DEFAULT}"
                        )
                        log_message(
                            f"[core]    INFO:  updating sqlite database from "
                            f"v{db_version} to v{VERSION} under: {Path.DATABASE}"
                        )
                        setup_new_database(quiet=quiet)
                        conn.cursor().execute(
                            'UPDATE system SET value=? WHERE variable="db_version";',
                            (VERSION,),
                        )
                        conn.commit()
                        conn.close()
                        if db_version < "2.4.0":
                            update_database_from_2_3_0(quiet=quiet)
                        if db_version < "2.5.0":
                            update_database_from_2_4_1(quiet=quiet)
                        if db_version < "2.7.0":
                            update_database_from_2_6_1(quiet=quiet)
                        if db_version < "2.7.2":
                            update_database_from_2_7_1(quiet=quiet)
            else:
                update_database_from_1_3_2(quiet=quiet)

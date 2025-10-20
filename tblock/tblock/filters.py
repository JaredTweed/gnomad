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
import io
import os.path
import sqlite3
import json
import hashlib
import lzma
import gzip
import warnings
import shutil
from colorama import Fore, Style

# Local modules
from .const import (
    WARNS,
    RulePolicy,
    USER_RULE_PRIORITY,
    Profile,
    Components,
    FilterPermissions,
)
from .style import Icon, Font, loading_icon
from .config import Path, Var
from .utils import (
    fetch_file,
    prompt_user,
    is_url,
    check_root_access,
    lock_db,
    unlock_db,
    get_user_response,
    owner_is_root,
)
from .exceptions import FilterError, RepoError, FilterSyntaxError
from .converter import detect_syntax, FilterParser, ALL_SYNTAX
from .hosts import update_hosts
from .rules import Rule, __remove_allowed_matches

# To avoid confusion when updating the filter list repository
from .config import VERSION as TBLOCK_VERSION


class Filter:
    def __init__(
        self, filter_id: str, quiet: bool = False, custom_source: str = None
    ) -> None:
        """
        Filter list object

        :param filter_id: The ID of the filter list
        :param quiet: Optional. Do not display an output (false by default)
        :param custom_source: Optional. Specify the source for a custom filter list
        """
        self.id = str(filter_id)
        self.quiet = quiet

        # Fetch filter list data from the database
        with sqlite3.connect(Path.DATABASE) as conn:
            data = (
                conn.cursor()
                .execute(
                    "SELECT source, metadata, subscribing, on_repo, mirrors, syntax, rules_count "
                    "FROM filters WHERE id=?;",
                    (self.id,),
                )
                .fetchone()
            )

        self.exists = bool(data)

        if self.exists:
            self.source = data[0]
        elif custom_source and not self.exists:
            self.source = custom_source
        else:
            self.source = None

        # Check if the filter list source exists
        with sqlite3.connect(Path.DATABASE) as conn:
            check = (
                conn.cursor()
                .execute("SELECT id FROM filters WHERE source=?;", (self.source,))
                .fetchone()
            )
        if check:
            self.source_exists = True
        else:
            self.source_exists = False

        self.metadata = json.loads(data[1]) if self.exists else {}
        self.subscribing = bool(data[2]) if self.exists else False
        self.on_repo = bool(data[3]) if self.exists else False
        self.mirrors = json.loads(data[4]) if (self.exists and data[4]) else {}
        self.syntax = data[5] if self.exists else None
        self.rules_count = data[6] if self.exists and data[6] else 0
        self.tmp_file = os.path.join(
            Path.TMP_DIR, self.id.replace(":", "_").replace("/", "_").replace("?", "_")
        )
        self.cache_file = os.path.join(
            Path.CACHE, self.id.replace(":", "_").replace("/", "_").replace("?", "_")
        )

    @property
    def permissions(self) -> FilterPermissions:
        warnings.warn(
            "This property is no longer useful, since permissions do not exist anymore.",
            DeprecationWarning,
        )
        return FilterPermissions("AB") if self.exists else None

    def retrieve_mirror(self, mirror: str, compression: str = None) -> bool:
        """
        Retrieve a mirror of a filter list when the main location is unreachable

        :param mirror: The mirror to retrieve
        :param compression: Optional. Specify the compression algorithm for the mirror (xz/gzip)

        :return: bool. True if the filter list has been retrieved successfully from the mirror
        """
        if fetch_file(mirror, "mirror: " + self.id, self.tmp_file, self.quiet):
            if compression is None:
                return True
            elif compression == "xz":
                # Decompress XZ-compressed filter list
                __msg = "Decompressing filter list: {0} (xz)".format(self.id)
                if not self.quiet:
                    print(f" {loading_icon(1)} {__msg}", end="\r")
                with open(self.tmp_file, "rb") as f:
                    filter_list_content = lzma.decompress(
                        f.read(), format=lzma.FORMAT_XZ
                    )
                if not self.quiet:
                    print(f" {loading_icon(2)} {__msg}", end="\r")
                with open(self.tmp_file, "wb") as w:
                    w.write(filter_list_content)
                if not self.quiet:
                    print(f" {Icon.SUCCESS} {__msg}")
                return True
            elif compression == "gzip":
                # Decompress gzip-compressed filter list
                __msg = "Decompressing filter list: {0} (gzip)".format(self.id)
                if not self.quiet:
                    print(f" {loading_icon(1)} {__msg}", end="\r")
                with open(self.tmp_file, "rb") as f:
                    filter_list_content = gzip.decompress(f.read())
                if not self.quiet:
                    print(f" {loading_icon(2)} {__msg}", end="\r")
                with open(self.tmp_file, "wb") as w:
                    w.write(filter_list_content)
                if not self.quiet:
                    print(f" {Icon.SUCCESS} {__msg}")
                return True
            else:
                raise FilterError(
                    "compression algorithm is currently unsupported: {0}".format(
                        compression
                    )
                )
        else:
            return False

    def cache_exists(self) -> bool:
        """
        Check if the filter list already exists in cache
        """
        return os.path.exists(self.cache_file)

    def cache_is_up_to_date(self) -> bool:
        """
        Compare the downloaded filter list with the one stored in cache and check if filter list is already up-to-date
        """
        if self.cache_exists():
            with open(self.tmp_file, "rb") as f:
                tmp_md5sum = hashlib.sha512(f.read())
            with open(self.cache_file, "rb") as f:
                cache_md5sum = hashlib.sha512(f.read())
            return bool(tmp_md5sum.hexdigest() == cache_md5sum.hexdigest())
        else:
            return False

    def get_rules_count(self) -> int:
        """
        Get the number of rules that are set by filter list
        """
        if not self.subscribing:
            raise FilterError("not subscribing to filter list: {0}".format(self.id))
        else:
            with sqlite3.connect(Path.DATABASE) as db:
                data = (
                    db.cursor()
                    .execute("SELECT COUNT() FROM rules WHERE filter_id=?;", (self.id,))
                    .fetchone()
                )
            return int(data[0])

    def delete_cache(self) -> None:
        """
        Delete the filter list stored in cache
        """
        __msg = "Removing cache: {0}".format(self.id)
        if not self.quiet:
            print(f" {loading_icon(1)} {__msg}", end="\r")
        if self.cache_exists():
            if not self.quiet:
                print(f" {Icon.SUCCESS} {__msg}")
            os.remove(self.cache_file)
            try:
                with sqlite3.connect(Path.DATABASE) as conn:
                    conn.cursor().execute("DELETE FROM cache WHERE key=?", (self.id,))
            except sqlite3.OperationalError:
                pass
        elif not self.quiet:
            print(f" {Icon.WARNING} Cache does not exist: {self.id}")

    def retrieve(self) -> None:
        """
        Retrieve a filter list
        """
        if not self.exists:
            raise FilterError("filter list not found: {0}".format(self.id))
        else:
            if not fetch_file(self.source, self.id, self.tmp_file, self.quiet):
                for mirror in self.mirrors.keys():
                    if "compression" in self.mirrors[mirror].keys():
                        if self.retrieve_mirror(
                            mirror, compression=self.mirrors[mirror]["compression"]
                        ):
                            break
                    else:
                        if self.retrieve_mirror(mirror):
                            break
                else:
                    try:
                        with sqlite3.connect(Path.DATABASE) as conn:
                            real_hash = (
                                conn.cursor()
                                .execute(
                                    "SELECT sha512 FROM cache WHERE key=?", (self.id,)
                                )
                                .fetchone()
                            )
                    except sqlite3.OperationalError:
                        real_hash = [""]
                    if real_hash is None:
                        real_hash = [""]
                    if not fetch_file(
                        self.cache_file,
                        "cache: " + self.id,
                        self.tmp_file,
                        self.quiet,
                        sha512sum=real_hash[0],
                    ):
                        raise FilterError(
                            "unable to retrieve filter list: {0}".format(self.id)
                        )

    def update(self, force: bool = False) -> None:
        """
        Update the rules from a filter list (requires to be downloaded before)

        :param force: Optional. Force updating, even if filter list is up-to-date
        """
        if not os.path.isfile(self.tmp_file):
            raise FilterError(
                "filter list needs to be downloaded before updating its rules"
            )
        elif (
            self.cache_is_up_to_date()
            and self.get_rules_count() == self.rules_count
            and not force
        ):
            if not self.quiet:
                print(f" {Icon.INFORMATION} " + "Nothing to update")
        else:
            # Remove rules from this filter lists
            if self.rules_count != 0:
                self.delete_all_rules()

            if self.syntax is None:
                with io.open(self.tmp_file, "rt") as f:
                    lines = f.readlines()
                    if not self.quiet:
                        __msg = "Detecting filter list syntax"
                        print(f" {loading_icon(1)} {__msg}", end="\r")
                    self.syntax = detect_syntax(lines)
                    with sqlite3.connect(Path.DATABASE) as conn:
                        conn.cursor().execute(
                            "UPDATE filters SET syntax=? WHERE id=?",
                            (self.syntax, self.id),
                        )
                    if not self.quiet:
                        print(f" {Icon.SUCCESS} {__msg}")
                        print(
                            f" {Icon.INFORMATION} "
                            + "Filter list syntax is: {0}".format(self.syntax)
                        )

            parser = FilterParser(self.tmp_file, self.syntax, self.quiet)
            parser.insert_rules_to_database(self.id)

            # Move downloaded filter list to cache and insert its hash into the database
            with open(self.tmp_file, "rb") as f:
                content = f.read()
            shasum = hashlib.sha512(content).hexdigest()
            with sqlite3.connect(Path.DATABASE) as conn:
                try:
                    conn.cursor().execute(
                        "INSERT INTO cache (key, sha512) VALUES (?, ?);",
                        (self.id, shasum),
                    )
                except sqlite3.IntegrityError:
                    conn.cursor().execute(
                        "UPDATE cache SET sha512=? WHERE key=?;", (shasum, self.id)
                    )
                conn.commit()

            shutil.copy(self.tmp_file, self.cache_file)

            # Store initial rule count
            with sqlite3.connect(Path.DATABASE) as conn:
                conn.cursor().execute(
                    "UPDATE filters SET rules_count=? WHERE id=?",
                    (self.get_rules_count(), self.id),
                )
                conn.commit()

            # Delete temporary file
            os.remove(self.tmp_file)

    def delete_all_rules(self) -> None:
        """
        Delete all rules that are set by the filter list
        """
        __msg = "Deleting previous rules:"
        if not self.quiet:
            print(f" {loading_icon(1)} {__msg} 0", end="\r")
        with sqlite3.connect(Path.DATABASE) as conn:
            conn.cursor().execute('DELETE FROM "rules" WHERE filter_id=?;', (self.id,))
            conn.cursor().execute(
                "UPDATE filters SET rules_count=? WHERE id=?;", (None, self.id)
            )
            conn.commit()
            total_changes = conn.total_changes - 1
        if not self.quiet:
            print(f" {Icon.SUCCESS} {__msg} {total_changes}")

    def subscribe(self, permissions=None) -> None:
        """
        Mark the filter list as "subscribed" in the database

        :param permissions: Deprecated parameter only kept for compatibility purposes
        """
        if not os.path.isfile(self.tmp_file):
            raise FilterError(
                "filter list needs to be downloaded before updating its rule"
            )
        elif self.subscribing:
            if not self.quiet:
                print(f" {Icon.WARNING} Already subscribing to filter list: {self.id}")
        else:
            __msg = f"Subscribing to: {self.id}"
            if not self.quiet:
                print(f" {loading_icon(1)} {__msg}", end="\r")
            with sqlite3.connect(Path.DATABASE) as conn:
                conn.cursor().execute(
                    "UPDATE filters SET subscribing=? WHERE id=?",
                    (int(True), self.id),
                )
                self.subscribing = True
            if not self.quiet:
                if self.on_repo:
                    if (
                        "deprecated" in self.metadata.keys()
                        and self.metadata["deprecated"]
                    ):
                        print(f" {Icon.WARNING} Warning: {self.id} is deprecated")
                print(f" {Icon.SUCCESS} {__msg}")

    def change_permissions(self, permissions=None) -> None:
        """
        Deprecated method only kept for compatibility purposes
        """
        warnings.warn(
            "This method is no longer useful, since permissions do not exist anymore.",
            DeprecationWarning,
        )

    def add_custom(self, custom_syntax: str = None) -> None:
        """
        Add custom filter lists to database

        :param custom_syntax: Optional. Specify the syntax of the custom filter list

        Note:
            This function doesn't mark the list as "subscribed".
            You still need to use the function `self.subscribe()` in order to subscribe to the filter list.
        """
        if self.exists:
            raise FilterError("filter list already exists: {0}".format(self.id))
        elif self.source_exists:
            raise FilterError(
                "filter list source already exists: {0}".format(self.source)
            )
        elif custom_syntax is not None and custom_syntax not in ALL_SYNTAX:
            raise FilterSyntaxError("invalid syntax: {0}".format(custom_syntax))
        elif self.id == USER_RULE_PRIORITY:
            raise FilterError(
                "filter list cannot have the same ID than user rules: {0}".format(
                    self.id
                )
            )
        elif not self.source:
            raise FilterError("invalid source: {0}".format(self.source))
        else:
            # Get the real path of the file if it is a local file
            if not is_url(self.source):
                self.source = os.path.realpath(self.source)
                if not os.path.isfile(self.source):
                    raise FileNotFoundError("file not found: {0}".format(self.source))
                elif not owner_is_root(self.source):
                    raise FilterError(
                        "for security reasons, file owner must be root: {0}".format(
                            self.source
                        )
                    )

            __msg = "Inserting filter list into database:"
            if not self.quiet:
                print(f" {loading_icon(1)} {__msg} {self.id}", end="\r")
            with sqlite3.connect(Path.DATABASE) as conn:
                conn.cursor().execute(
                    "INSERT INTO filters (id, source, metadata, subscribing, on_repo, mirrors, syntax)"
                    "VALUES (?, ?, ?, ?, ?, ?, ?);",
                    (
                        self.id,
                        self.source,
                        json.dumps({}),
                        int(False),
                        int(False),
                        json.dumps({}),
                        custom_syntax,
                    ),
                )
            self.exists = True
            self.syntax = custom_syntax
            if not self.quiet:
                print(f" {Icon.SUCCESS} {__msg} {self.id}")

    def unsubscribe(self) -> None:
        """
        Mark a filter as "unsubscribed" in the database
        """
        if not self.subscribing and self.on_repo:
            if not self.quiet:
                print(" {Icon.WARNING} " + "Not subscribing to filter list")
        else:
            self.delete_all_rules()
            if self.on_repo:
                __msg = f"Removing: {self.id}"
                if not self.quiet:
                    print(f" {loading_icon(1)} {__msg}", end="\r")
                with sqlite3.connect(Path.DATABASE) as conn:
                    conn.cursor().execute(
                        "UPDATE filters SET subscribing=? WHERE id=?",
                        (int(False), self.id),
                    )
                self.__init__(self.id, quiet=self.quiet)
                if not self.quiet:
                    print(f" {Icon.SUCCESS} {__msg}")
            else:
                __msg = "Removing filter list from database"
                if not self.subscribing and not self.quiet:
                    print(f" {Icon.WARNING} " + "Not subscribing to custom filter list")
                if not self.quiet:
                    print(f" {loading_icon(1)} {__msg}", end="\r")
                with sqlite3.connect(Path.DATABASE) as conn:
                    conn.cursor().execute("DELETE FROM filters WHERE id=?", (self.id,))
                self.__init__(self.id, quiet=self.quiet, custom_source=self.source)
                if not self.quiet:
                    print(f" {Icon.SUCCESS} {__msg}")
            # self.delete_cache()

    def rename_custom(self, filter_id: str) -> None:
        """
        Change the ID of a custom filter list

        :param filter_id: The new ID to use
        """
        if self.on_repo:
            if not self.quiet:
                print(f" {Icon.WARNING} Not a custom filter list: {self.id}")
        elif not self.subscribing:
            if not self.quiet:
                print(f" {Icon.WARNING} Not subscribing to filter list")
        elif Filter(filter_id).exists:
            raise FilterError("filter list ID already exists: {0}".format(filter_id))
        elif filter_id == USER_RULE_PRIORITY:
            raise FilterError(
                "filter list cannot have the same ID than user rules: {0}".format(
                    self.id
                )
            )
        else:
            __msg = "Changing ID of filter list:"
            if not self.quiet:
                print(f" {loading_icon(1)} {__msg} {self.id}", end="\r")
            with sqlite3.connect(Path.DATABASE) as conn:
                conn.cursor().execute(
                    "UPDATE filters SET id=? WHERE id=?", (filter_id, self.id)
                )
                conn.cursor().execute(
                    "UPDATE rules SET filter_id=? WHERE filter_id=?",
                    (filter_id, self.id),
                )
                self.id = filter_id
            if not self.quiet:
                print(f" {Icon.SUCCESS} {__msg} {self.id}")


def __check_filter_lists_validity_to_subscribe(
    filter_lists: list, custom_sources: list = None
) -> bool:
    """
    Check every filter list of a list and returns True if all filter lists exist or are custom

    :param filter_lists: The list of filter lists to check
    :param custom_sources: Optional. If custom, list containing sources, ordered in the same order as filter lists

    :return: bool. True if all filter lists exist or are custom. Otherwise, raise a FilterError
    """
    if custom_sources is not None and len(filter_lists) != len(custom_sources):
        raise FilterError("one filter list ID should be provided for each source")
    for filter_id in filter_lists:
        # Define filter list object
        if custom_sources:
            filter_object = Filter(
                filter_id, custom_sources[filter_lists.index(filter_id)]
            )
        else:
            filter_object = Filter(filter_id)
        if not filter_object.exists and not custom_sources:
            raise FilterError("filter list does not exists: {0}".format(filter_id))
        elif filter_object.exists and custom_sources:
            raise FilterError("filter list already exists: {0}".format(filter_id))
    else:
        return True


def __check_filter_lists_validity_exists(filter_lists: list) -> bool:
    """
    Check every filter list of a list and returns True if all filter lists exist

    :param filter_lists: The list of filter lists to check

    :return: bool. True if all filter lists exist. Otherwise, raise a FilterError
    """
    for filter_id in filter_lists:
        if not Filter(filter_id).exists:
            raise FilterError("filter list does not exists: {0}".format(filter_id))
    else:
        return True


def __check_filter_lists_validity_subscribed(filter_lists: list) -> bool:
    """
    Check every filter list of a list and returns True if all filter lists are marked as "subscribed" in the database

    :param filter_lists: The list of filter lists to check

    :return: bool. True if all filter lists are subscribed. Otherwise, raise a FilterError
    """
    for filter_id in filter_lists:
        filter_object = Filter(filter_id)
        if not filter_object.exists:
            raise FilterError("filter list does not exists: {0}".format(filter_id))
        elif not filter_object.subscribing and filter_object.on_repo:
            raise FilterError("not subscribing to filter list: {0}".format(filter_id))
    else:
        return True


def __retrieve_filter_lists(filter_lists: list, quiet: bool = False) -> None:
    """
    Retrieve all filter lists of a list$

    :param filter_lists: The list of filter lists to retrieve
    :param quiet: Optional. Do not display an output (false by default)
    """
    if not quiet:
        print(f"{Font.BOLD}==> Retrieving filter lists{Font.DEFAULT}")
    for filter_id in filter_lists:
        filter_object = Filter(filter_id, quiet)
        filter_object.retrieve()


def get_all_filter_lists(
    subscribing_only: bool = False,
    not_subscribing_only: bool = False,
    from_repo_only: bool = False,
    custom_only: bool = False,
    blacklist: list = None,
) -> list:
    """
    Get a list of all filter lists

    :param subscribing_only: Optional. List only subscribed filter lists
    :param not_subscribing_only: Optional. List only filter lists that are not subscribed
    :param from_repo_only: Optional. List only filter lists that are available on the filter list repository
    :param custom_only: Optional. List only custom filter lists
    :param blacklist: Optional. Ignore specified filter lists
    """
    if subscribing_only and not_subscribing_only or from_repo_only and custom_only:
        return []
    elif not os.path.isfile(Path.DATABASE):
        raise FileNotFoundError(
            "database does not exist yet. "
            "Please run 'tblock -Y' with admin privileges to create it"
        )
    else:
        with sqlite3.connect(Path.DATABASE) as conn:
            if subscribing_only and from_repo_only:
                data = conn.execute(
                    "SELECT id FROM filters WHERE subscribing=1 AND on_repo=1 ORDER BY id ASC;"
                )
            elif subscribing_only and custom_only:
                data = conn.execute(
                    "SELECT id FROM filters WHERE subscribing=1 AND on_repo=0 ORDER BY id ASC;"
                )
            elif subscribing_only:
                data = conn.execute(
                    "SELECT id FROM filters WHERE subscribing=1 ORDER BY id ASC;"
                )
            elif not_subscribing_only and from_repo_only:
                data = conn.execute(
                    "SELECT id FROM filters WHERE subscribing=0 AND on_repo=1 ORDER BY id ASC;"
                )
            elif not_subscribing_only and custom_only:
                data = conn.execute(
                    "SELECT id FROM filters WHERE subscribing=0 AND on_repo=0 ORDER BY id ASC;"
                )
            elif not_subscribing_only:
                data = conn.execute(
                    "SELECT id FROM filters WHERE subscribing=0 ORDER BY id ASC;"
                )
            elif custom_only:
                data = conn.execute(
                    "SELECT id FROM filters WHERE on_repo=0 ORDER BY id ASC;"
                )
            elif from_repo_only:
                data = conn.execute(
                    "SELECT id FROM filters WHERE on_repo=1 ORDER BY id ASC;"
                )
            else:
                data = conn.execute("SELECT id FROM filters ORDER BY id ASC;")
        output_list = []
        for row in data:
            if blacklist and row[0] in blacklist:
                pass
            else:
                output_list.append(row[0])
        return output_list


def delete_all_cache(quiet: bool = False) -> None:
    """
    Delete the whole filter lists cache

    :param quiet: Optional. Do not display an output (false by default)
    """
    __msg = "Deleting filter lists cache"
    if not quiet:
        print(f" {loading_icon(1)} {__msg}", end="\r")
    conn = sqlite3.connect(Path.DATABASE)
    for filename in os.listdir(Path.CACHE):
        try:
            conn.cursor().execute("DELETE FROM cache WHERE key=?", (filename,))
        except sqlite3.OperationalError:
            pass
        os.remove(os.path.join(Path.CACHE, filename))
    conn.commit()
    conn.close()
    if not quiet:
        print(f" {Icon.SUCCESS} {__msg}")


def subscribe(
    filter_lists: list,
    do_not_prompt: bool = False,
    quiet: bool = False,
    sync_repo: bool = False,
    full_update: bool = False,
    force: bool = False,
    rebuild_hosts: bool = True,
    permissions=None,
) -> None:
    """
    Subscribe to a given list of filter lists

    :param filter_lists: The filter lists IDs
    :param do_not_prompt: Optional. Do not prompt before subscribing (false by default)
    :param quiet: Optional. Do not display an output (false by default)
    :param sync_repo: Optional. Also sync the filter lists repository before subscribing (false by default)
    :param full_update: Optional. Also update all filter lists before subscribing (false by default)
    :param force: Optional. Force updating, even if filter list or the filter list repository is up-to-date
    :param rebuild_hosts: Optional. Rebuild the hosts file after the operation is done (true by default)
    :param permissions: Deprecated parameter only kept for compatibility purposes
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock database
    lock_db()

    # Check all filter lists
    if not sync_repo:
        if get_current_repo_index_version() == 0 and not quiet:
            print(
                f"{Fore.YELLOW}Warning: repository index is not synced. Run tblock -Y to sync now.{Style.RESET_ALL}"
            )
        if __check_filter_lists_validity_to_subscribe(filter_lists):
            # Prompt the user before continuing
            if do_not_prompt or prompt_user(
                "You are about to subscribe to the following filters:", filter_lists
            ):
                if full_update:
                    update_all(
                        do_not_prompt=True,
                        quiet=quiet,
                        sync_repo=False,
                        force=force,
                        blacklist=filter_lists,
                        rebuild_hosts=False,
                        lock_database=False,
                    )
                # Then, retrieve them
                __retrieve_filter_lists(filter_lists, quiet)
                # Mark filter lists as subscribed in the database and update them
                for filter_id in filter_lists:
                    if not quiet:
                        print(
                            f"{Font.BOLD}==> Subscribing to filter list: {filter_id}{Font.DEFAULT}"
                        )
                    filter_object = Filter(filter_id, quiet)
                    filter_object.subscribe()
                    filter_object.update(force=force)
                __remove_allowed_matches(quiet)
                if rebuild_hosts:
                    update_hosts(quiet=quiet)

    else:
        # This condition is required because in the following situation:
        # if the user wants to subscribe to a filter list available in the new index but not in the local database
        # That way, TBlock syncs the repository before and no error is triggered.
        # This is mainly useful right after the installation, if the user runs: "tblock -Sy tblock-base"
        if do_not_prompt or prompt_user(
            "You are about to subscribe to the following filters:", filter_lists
        ):
            sync_filter_list_repo(force=force, quiet=quiet, lock_database=False)
            if __check_filter_lists_validity_to_subscribe(filter_lists):
                if full_update:
                    update_all(
                        do_not_prompt=True,
                        quiet=quiet,
                        sync_repo=False,
                        force=force,
                        blacklist=filter_lists,
                        rebuild_hosts=False,
                        lock_database=False,
                    )
                # Then, retrieve them
                __retrieve_filter_lists(filter_lists, quiet)
                # Mark filter lists as subscribed in the database and update them
                for filter_id in filter_lists:
                    if not quiet:
                        print(
                            f"{Font.BOLD}==> Subscribing to filter list: {filter_id}{Font.DEFAULT}"
                        )
                    filter_object = Filter(filter_id, quiet)
                    filter_object.subscribe()
                    filter_object.update(force=force)
                __remove_allowed_matches(quiet)
                if rebuild_hosts:
                    update_hosts(quiet=quiet)

    # Unlock the database
    unlock_db()


def change_permissions(
    filter_lists: list,
    permissions,
    do_not_prompt: bool = False,
    quiet: bool = False,
    sync_repo: bool = False,
    full_update: bool = False,
    force: bool = False,
    rebuild_hosts: bool = True,
) -> None:
    """
    Deprecated function only kept for compatibility purposes
    """
    warnings.warn(
        "This function is no longer useful, since permissions do not exist anymore.",
        DeprecationWarning,
    )


def rename_custom(
    filter_lists: list,
    do_not_prompt: bool = False,
    quiet: bool = False,
    sync_repo: bool = False,
    full_update: bool = False,
    force: bool = False,
    rebuild_hosts: bool = True,
) -> None:
    """
    Change the ID of a given list of custom filter lists

    :param filter_lists: The filter lists IDs, followed by new IDs, like: `["old_id1", "new_id1", "old_id2", "new_id2"]`
    :param do_not_prompt: Optional. Do not prompt before subscribing (false by default)
    :param quiet: Optional. Do not display an output (false by default)
    :param sync_repo: Optional. Also sync the filter lists repository before subscribing (false by default)
    :param full_update: Optional. Also update all filter lists before subscribing (false by default)
    :param force: Optional. Force updating, even if filter list or the filter list repository is up-to-date
    :param rebuild_hosts: Optional. Rebuild the hosts file after the operation is done (true by default)
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    lock_db()

    # Separate filter lists from their future IDs
    count = 0
    new_ids = []
    old_ids = []
    for element in filter_lists:
        if count % 2 != 0 and count != 0:
            new_ids.append(element)
        else:
            old_ids.append(element)
        count += 1
    filter_lists = old_ids

    # Check all filter lists
    if __check_filter_lists_validity_subscribed(filter_lists):
        # Prompt the user before continuing
        if do_not_prompt or prompt_user(
            "You are about to change the IDs of the following filters:", filter_lists
        ):
            # Sync the upstream filter lists repository if needed
            if sync_repo:
                sync_filter_list_repo(force=force, quiet=quiet, lock_database=False)

            if full_update:
                update_all(
                    do_not_prompt=True,
                    quiet=quiet,
                    sync_repo=False,
                    force=force,
                    rebuild_hosts=False,
                    lock_database=False,
                )
            # Change filter lists ID
            if not quiet:
                print(f"{Font.BOLD}==> Renaming filter lists{Font.DEFAULT}")
            for filter_id in filter_lists:
                filter_object = Filter(filter_id, quiet)
                filter_object.rename_custom(new_ids[filter_lists.index(filter_id)])
            if full_update and rebuild_hosts:
                # If only the name of the filter changed, no need to update
                update_hosts(quiet=quiet)

    # Unlock the database
    unlock_db()


def subscribe_custom(
    filter_lists: list,
    do_not_prompt: bool = False,
    quiet: bool = False,
    sync_repo: bool = False,
    full_update: bool = False,
    force: bool = False,
    custom_syntax: str = None,
    rebuild_hosts: bool = True,
    permissions=None,
) -> None:
    """
    Subscribe to a given list of filter lists

    :param filter_lists: The filter lists IDs, followed by custom sources, like:
        `["custom_1", "https://example.org/1.txt", "custom_2", "ftp://ftp.example.com/2.txt"]`
    :param do_not_prompt: Optional. Do not prompt before subscribing (false by default)
    :param quiet: Optional. Do not display an output (false by default)
    :param sync_repo: Optional. Also sync the filter lists repository before subscribing (false by default)
    :param full_update: Optional. Also update all filter lists before subscribing (false by default)
    :param force: Optional. Force updating, even if filter list or the filter list repository is up-to-date
    :param custom_syntax: Optional. Specify the syntax of the custom filter list
    :param rebuild_hosts: Optional. Rebuild the hosts file after the operation is done (true by default)
    :param permissions: Deprecated parameter only kept for compatibility purposes
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    lock_db()

    # Separate filter lists from their sources
    count = 0
    filter_sources = []
    _filter_lists = []
    for element in filter_lists:
        if count % 2 != 0 and count != 0:
            filter_sources.append(element)
        else:
            _filter_lists.append(element)
        count += 1
    filter_lists = _filter_lists

    # Check all filter lists
    if __check_filter_lists_validity_to_subscribe(
        filter_lists, custom_sources=filter_sources
    ):
        # Prompt the user before continuing
        if do_not_prompt or prompt_user(
            "You are about to subscribe to the following filters:", filter_lists
        ):
            # Sync the upstream filter lists repository if needed
            if sync_repo:
                sync_filter_list_repo(force=force, quiet=quiet, lock_database=False)

            if full_update:
                update_all(
                    do_not_prompt=True,
                    quiet=quiet,
                    sync_repo=False,
                    force=force,
                    rebuild_hosts=False,
                    lock_database=False,
                )
            # Add them to the database
            if not quiet:
                print(
                    f"{Font.BOLD}==> Adding custom filter lists to database{Font.DEFAULT}"
                )
            for filter_id in filter_lists:
                filter_object = Filter(
                    filter_id,
                    quiet,
                    custom_source=filter_sources[filter_lists.index(filter_id)],
                )
                filter_object.add_custom(custom_syntax)
            # Then, retrieve them
            __retrieve_filter_lists(filter_lists, quiet)
            # Mark filter lists as subscribed in the database and update them
            for filter_id in filter_lists:
                if not quiet:
                    print(
                        f"{Font.BOLD}==> Subscribing to filter list: {filter_id}{Font.DEFAULT}"
                    )
                filter_object = Filter(filter_id, quiet)
                filter_object.subscribe()
                filter_object.update(force=force)
            __remove_allowed_matches(quiet)
            if rebuild_hosts:
                update_hosts(quiet=quiet)

    # Unlock the database
    unlock_db()


def unsubscribe(
    filter_lists: list,
    do_not_prompt: bool = False,
    force: bool = False,
    quiet: bool = False,
    sync_repo: bool = False,
    full_update: bool = False,
    rebuild_hosts: bool = True,
) -> None:
    """
    Unsubscribe from a given list of filter lists

    :param filter_lists: The filter lists IDs
    :param do_not_prompt: Optional. Do not prompt before subscribing (false by default)
    :param force: Optional. Force updating, even if filter list or the filter list repository is up-to-date
    :param quiet: Optional. Do not display an output (false by default)
    :param sync_repo: Optional. Also sync the filter lists repository before subscribing (false by default)
    :param full_update: Optional. Also update all filter lists before subscribing (false by default)
    :param rebuild_hosts: Optional. Rebuild the hosts file after the operation is done (true by default)
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    lock_db()

    # Check all filter lists
    if __check_filter_lists_validity_subscribed(filter_lists):
        if do_not_prompt or prompt_user(
            "You are about to unsubscribe from the following filters:", filter_lists
        ):
            # Sync the upstream filter lists repository if needed
            if sync_repo:
                sync_filter_list_repo(force=force, quiet=quiet, lock_database=False)

            # Mark filter lists as unsubscribed in the database and delete them if they are not found upstream
            for filter_id in filter_lists:
                if not quiet:
                    print(
                        f"{Font.BOLD}==> Unsubscribing from filter list: {filter_id}{Font.DEFAULT}"
                    )
                filter_object = Filter(filter_id, quiet)
                filter_object.unsubscribe()
                filter_object.delete_cache()
            if full_update:
                update_all(
                    do_not_prompt=True,
                    quiet=quiet,
                    sync_repo=False,
                    force=force,
                    rebuild_hosts=False,
                    lock_database=False,
                )
                update_hosts(quiet=quiet)
            else:
                __remove_allowed_matches(quiet)
                if rebuild_hosts:
                    update_hosts(quiet=quiet)
                print(
                    f" {Icon.WARNING} Always remember to update all filter lists after this operation"
                )

    # Unlock the database
    unlock_db()


def update(
    filter_lists: list,
    do_not_prompt: bool = False,
    force: bool = False,
    quiet: bool = False,
    sync_repo: bool = False,
    rebuild_hosts: bool = True,
) -> None:
    """
    Update a given list of filter lists

    :param filter_lists: The filter lists IDs
    :param do_not_prompt: Optional. Do not prompt before subscribing (false by default)
    :param force: Optional. Force updating, even if filter list or the filter list repository is up-to-date
    :param quiet: Optional. Do not display an output (false by default)
    :param sync_repo: Optional. Also sync the filter lists repository before subscribing (false by default)
    :param rebuild_hosts: Optional. Rebuild the hosts file after the operation is done (true by default)
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    lock_db()

    # First, check all filter lists
    if __check_filter_lists_validity_subscribed(filter_lists) and filter_lists:
        # Prompt the user before continuing
        if do_not_prompt or prompt_user(
            "You are about to update to the following filters:", filter_lists
        ):
            # Sync the upstream filter lists repository if needed
            if sync_repo:
                sync_filter_list_repo(force=force, quiet=quiet, lock_database=False)
            # Then, retrieve them
            __retrieve_filter_lists(filter_lists, quiet)
            # Update all filter lists
            for filter_id in filter_lists:
                if not quiet:
                    print(
                        f"{Font.BOLD}==> Updating filter list: {filter_id}{Font.DEFAULT}"
                    )
                filter_object = Filter(filter_id, quiet)
                filter_object.update(force=force)
            __remove_allowed_matches(quiet)
            if rebuild_hosts:
                update_hosts(quiet=quiet)

    # Unlock the database
    unlock_db()


def update_all(
    do_not_prompt: bool = False,
    force: bool = False,
    quiet: bool = False,
    sync_repo: bool = False,
    blacklist: list = None,
    rebuild_hosts: bool = True,
    lock_database: bool = True,
) -> None:
    """
    Update all subscribed filter lists

    :param do_not_prompt: Optional. Do not prompt before subscribing (false by default)
    :param force: Optional. Force updating, even if filter list or the filter list repository is up-to-date
    :param quiet: Optional. Do not display an output (false by default)
    :param sync_repo: Optional. Also sync the filter lists repository before subscribing (false by default)
    :param blacklist: Optional. Filter list IDs to ignore
    :param rebuild_hosts: Optional. Update hosts file after updating filter lists (true by default)
    :param lock_database: Optional. Lock the database to avoid conflict with other running instances (true by default)
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    if lock_database:
        lock_db()

    filter_lists = get_all_filter_lists(subscribing_only=True, blacklist=blacklist)
    # First, check all filter lists
    if __check_filter_lists_validity_subscribed(filter_lists) and filter_lists:
        # Prompt the user before continuing
        if do_not_prompt or prompt_user(
            "You are about to update to the following filters:", filter_lists
        ):
            # Sync the upstream filter lists repository if needed
            if sync_repo:
                sync_filter_list_repo(force=force, quiet=quiet, lock_database=False)
            # Then, retrieve them
            __retrieve_filter_lists(filter_lists, quiet)
            # Update all filter lists
            for filter_id in filter_lists:
                if not quiet:
                    print(
                        f"{Font.BOLD}==> Updating filter list: {filter_id}{Font.DEFAULT}"
                    )
                filter_object = Filter(filter_id, quiet)
                filter_object.update(force=force)
            __remove_allowed_matches(quiet)
            if rebuild_hosts:
                update_hosts(quiet=quiet)

    # Unlock the database
    if lock_database:
        unlock_db()


def show_info(filter_lists: list, quiet: bool = False) -> None:
    """
    Print information about a given list of filter lists

    :param filter_lists: The filter lists IDs
    :param quiet: Optional. Do not display an output (false by default)
    """

    # First, check all filter lists
    if not os.path.isfile(Path.DATABASE):
        raise FileNotFoundError(
            "database does not exist yet. "
            "Please run 'tblock -Y' with admin privileges to create it"
        )
    elif __check_filter_lists_validity_exists(filter_lists) and filter_lists:
        # Show information about filter lists
        print("------------------------------------")
        for filter_id in filter_lists:
            filter_object = Filter(filter_id)
            print(f"{Font.BOLD}Filter ID       : {Font.DEFAULT}{filter_id}")
            if filter_object.on_repo:
                print(
                    f"{Font.BOLD}Title           : {Font.DEFAULT}{filter_object.metadata['title']}"
                )
            print(f"{Font.BOLD}Source          : {Font.DEFAULT}{filter_object.source}")
            if filter_object.subscribing:
                print(f"{Font.BOLD}Subscribing     : {Font.DEFAULT}yes")
                print(
                    f"{Font.BOLD}Syntax          : {Font.DEFAULT}{filter_object.syntax}"
                )
                print(
                    f"{Font.BOLD}Active rules    : {Font.DEFAULT}{filter_object.rules_count}"
                )
            elif filter_object.on_repo:
                print(f"{Font.BOLD}Subscribing     : {Font.DEFAULT}no")
                print(
                    f"{Font.BOLD}Syntax          : {Font.DEFAULT}{filter_object.syntax}"
                )
            if filter_object.on_repo:
                print(
                    f"{Font.BOLD}Mirrors         : {Font.DEFAULT}{len(filter_object.mirrors)}"
                )
                print(f"{Font.BOLD}Custom          : {Font.DEFAULT}no")
                print(
                    f"{Font.BOLD}Homepage        : {Font.DEFAULT}{filter_object.metadata['homepage']}"
                )
                try:
                    print(
                        f"{Font.BOLD}License         : {Font.DEFAULT}{filter_object.metadata['license'][0]}"
                    )
                except IndexError:
                    print(
                        f"{Font.BOLD}License         : {Font.DEFAULT}{filter_object.metadata['license']}"
                    )
                try:
                    print(
                        f"{Font.BOLD}Status          : {Font.DEFAULT}{WARNS[filter_object.metadata['warning']]}"
                    )
                except KeyError:
                    pass
                if (
                    "deprecated" in filter_object.metadata.keys()
                    and filter_object.metadata["deprecated"]
                ):
                    print(f"{Font.BOLD}Deprecated      : {Font.DEFAULT}yes")

                tag_list = ""
                try:
                    for tag in filter_object.metadata["tags"]:
                        tag_list += tag + " "
                except KeyError:
                    pass
                print(f"{Font.BOLD}Tags            : {Font.DEFAULT}{tag_list}")
                print(
                    f"{Font.BOLD}Description     : {Font.DEFAULT}{filter_object.metadata['description']}"
                )
            else:
                print(f"{Font.BOLD}Custom          : {Font.DEFAULT}yes")
            print("------------------------------------")


def list_filter_lists(
    custom_only: bool = False,
    on_repo_only: bool = False,
    subscribing_only: bool = False,
    not_subscribing_only: bool = False,
    quiet: bool = False,
) -> None:
    """
    List filter lists stored in the database

    :param custom_only: List only custom filter lists
    :param on_repo_only: List only filter lists that are available on the filter list repository
    :param subscribing_only: List only filter lists that are marked as "subscribed" in the database
    :param not_subscribing_only: List only filter lists that are not marked as "subscribed" in the database
    :param quiet: Don't print verbose output
    """
    for f in get_all_filter_lists(
        subscribing_only=subscribing_only,
        not_subscribing_only=not_subscribing_only,
        custom_only=custom_only,
        from_repo_only=on_repo_only,
    ):
        show_search_info_filter_list(Filter(f), quiet)


def show_search_info_filter_list(filter_list: Filter, quiet: bool = False):
    if quiet:
        print(filter_list.id)
    elif filter_list.on_repo:
        subscribing = (
            f"{Font.BOLD}{Fore.GREEN}[subscribing]{Style.RESET_ALL}"
            if filter_list.subscribing
            else ""
        )
        if len(filter_list.metadata["description"]) > 90:
            desc = filter_list.metadata["description"][:90] + " ..."
        else:
            desc = filter_list.metadata["description"]
        print(
            f"{Font.BOLD}{filter_list.id}{Font.DEFAULT}: "
            f"{filter_list.metadata['title']} {subscribing}\n    {desc}"
        )
    else:
        print(
            f"{Font.BOLD}{filter_list.id}{Font.DEFAULT}: "
            f"(no title) {Font.BOLD}{Fore.BLUE}[custom]{Style.RESET_ALL}\n    (no description)"
        )


def search_filter_lists(
    query: str,
    custom_only: bool = False,
    on_repo_only: bool = False,
    subscribing_only: bool = False,
    not_subscribing_only: bool = False,
    quiet: bool = False,
) -> None:
    """
    Search across filter lists (and their metadata) stored in the database

    :param query: The search query to use
    :param custom_only: List only custom filter lists
    :param on_repo_only: List only filter lists that are available on the filter list repository
    :param subscribing_only: List only filter lists that are marked as "subscribed" in the database
    :param not_subscribing_only: List only filter lists that are not marked as "subscribed" in the database
    :param quiet: Don't print verbose output
    """
    regex_query = re.compile(query, re.IGNORECASE)

    filters_list = get_all_filter_lists(
        subscribing_only=subscribing_only,
        not_subscribing_only=not_subscribing_only,
        custom_only=custom_only,
        from_repo_only=on_repo_only,
    )

    for filter_id in filters_list:
        filter_match = Filter(filter_id)
        if re.findall(regex_query, filter_match.id):
            show_search_info_filter_list(filter_match, quiet)
        elif filter_match.on_repo and re.findall(
            regex_query, filter_match.metadata["title"]
        ):
            show_search_info_filter_list(filter_match, quiet)
        elif filter_match.on_repo and re.findall(
            regex_query, filter_match.metadata["description"]
        ):
            show_search_info_filter_list(filter_match, quiet)
        elif filter_match.on_repo:
            for tag in filter_match.metadata["tags"]:
                if filter_match.on_repo and re.findall(regex_query, tag):
                    show_search_info_filter_list(filter_match, quiet)
                    break


def get_search_results_filter_lists(
    query: str,
    custom_only: bool = False,
    on_repo_only: bool = False,
    subscribing_only: bool = False,
    not_subscribing_only: bool = False,
) -> list:
    """
    Search across filter lists (and their metadata) stored in the database

    :param query: The search query to use
    :param custom_only: List only custom filter lists
    :param on_repo_only: List only filter lists that are available on the filter list repository
    :param subscribing_only: List only filter lists that are marked as "subscribed" in the database
    :param not_subscribing_only: List only filter lists that are not marked as "subscribed" in the database
    """
    regex_query = re.compile(query, re.IGNORECASE)

    filters_list = get_all_filter_lists(
        subscribing_only=subscribing_only,
        not_subscribing_only=not_subscribing_only,
        custom_only=custom_only,
        from_repo_only=on_repo_only,
    )
    output = []
    for filter_id in filters_list:
        filter_match = Filter(filter_id)
        if re.findall(regex_query, filter_match.id):
            output.append(filter_match.id)
        elif filter_match.on_repo and re.findall(
            regex_query, filter_match.metadata["title"]
        ):
            output.append(filter_match.id)
        elif filter_match.on_repo and re.findall(
            regex_query, filter_match.metadata["description"]
        ):
            output.append(filter_match.id)
        elif filter_match.on_repo:
            for tag in filter_match.metadata["tags"]:
                if filter_match.on_repo and re.findall(regex_query, tag):
                    output.append(filter_match.id)
                    break
    return output


def purge_cache(do_not_prompt: bool = False, quiet: bool = False) -> None:
    if do_not_prompt or prompt_user(
        "You are about to delete all the cached filter lists:"
    ):
        print(f"{Font.BOLD}==> Cleaning cache{Font.DEFAULT}")
        for filter_id in get_all_filter_lists():
            Filter(filter_id, quiet=quiet).delete_cache()


def query_domain_to_filter_list(domains: list, quiet: bool = False) -> None:
    for d in domains:
        domain_obj = Rule(d)
        if not domain_obj.exists:
            if not quiet:
                print(f" {Icon.WARNING} rule does not exist: {d}")
        else:
            origin = domain_obj.filter_id
            if domain_obj.policy == RulePolicy.ALLOW:
                print(f"{origin}: ALLOW {d}")
            elif domain_obj.policy == RulePolicy.BLOCK:
                print(f"{origin}: BLOCK {d}")
            elif domain_obj.policy == RulePolicy.REDIRECT:
                print(f"{origin}: REDIRECT {d} TO {domain_obj.ip}")


def get_current_repo_index_version() -> int:
    with sqlite3.connect(Path.DATABASE) as conn:
        try:
            return int(
                conn.cursor()
                .execute('SELECT value FROM system WHERE variable="repo_version";')
                .fetchone()[0]
            )
        except (IndexError, TypeError):
            return 0


def get_active_filter_lists_count() -> int:
    with sqlite3.connect(Path.DATABASE) as db:
        return (
            db.cursor()
            .execute("SELECT COUNT() FROM filters WHERE subscribing=1;")
            .fetchone()[0]
        )


def sync_filter_list_repo(
    quiet: bool = False, force: bool = False, lock_database: bool = True
) -> None:
    """
    Print information about a given list of filter lists

    :param quiet: Optional. Do not display an output (false by default)
    :param force: Optional. Force updating, even if the filter list repository is up-to-date
    """

    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    # Lock the database
    if lock_database:
        lock_db()

    # Download XML index and its SHA512SUM
    if not quiet:
        print(f"{Font.BOLD}==> Syncing filter list repository{Font.DEFAULT}")

    for mirror in Var.REPO_MIRRORS:
        if fetch_file(
            mirror,
            "filter list repository",
            os.path.join(Path.TMP_DIR, "index.json"),
            quiet=quiet,
        ) and fetch_file(
            mirror + ".sha512",
            "filter list repository checksum",
            os.path.join(Path.TMP_DIR, "index.json.sha512"),
            quiet=quiet,
        ):
            break
    else:
        raise RepoError("unable to retrieve filter list repository")

    # Verify the SHA512SUM
    __msg = "Verifying checksum"
    if not quiet:
        print(f" {loading_icon(1)} {__msg}", end="\r")
    with open(os.path.join(Path.TMP_DIR, "index.json"), "rb") as f:
        file_shasum = hashlib.sha512(f.read()).hexdigest()
    if not quiet:
        print(f" {loading_icon(2)} {__msg}", end="\r")
    with open(os.path.join(Path.TMP_DIR, "index.json.sha512"), "rt") as f:
        real_shasum = f.read().split(" ")[0]
    if not quiet:
        print(f" {loading_icon(3)} {__msg}", end="\r")
    if file_shasum == real_shasum:
        if not quiet:
            print(f" {Icon.SUCCESS} {__msg}")
    else:
        if not quiet:
            print(f" {Icon.ERROR} {__msg}")
        raise RepoError("wrong checksum for filter list repository")

    # Parse the JSON file
    __msg = "Checking repository version"
    if not quiet:
        print(f" {loading_icon(1)} {__msg}", end="\r")
    try:
        content = open(os.path.join(Path.TMP_DIR, "index.json"), "rt")
        data = json.load(content)
        content.close()
    except json.decoder.JSONDecodeError:
        if not quiet:
            print(f" {Icon.ERROR} {__msg}")
        raise RepoError("filter list index is not a valid JSON file")
    if "repo" not in data.keys():
        if not quiet:
            print(f" {Icon.ERROR} {__msg}")
        raise RepoError("filter list index is not a valid JSON file")

    new_repo_version = data["repo"]["version"]
    current_repo_version = get_current_repo_index_version()

    db = sqlite3.connect(Path.DATABASE)
    cursor = db.cursor()

    # Check if index is up-to-date
    if (
        len(str(current_repo_version)) >= 6
        and int(str(current_repo_version)[0:6]) >= int(data["repo"]["version"])
        and not force
    ):
        if not quiet:
            print(f" {Icon.SUCCESS} {__msg}")
            print(f" {Icon.INFORMATION} " + "Filter list repository is up-to-date")
        db.close()
        unlock_db()
    else:
        if not quiet:
            print(f" {Icon.SUCCESS} {__msg}")

        # Check if TBlock is compatible and if it has been updated upstream
        __msg = "Checking compatibility"
        try:
            min_tblock_compat = int(data["repo"]["min_compat"].replace(".", ""))
            tblock_latest = str(data["repo"]["latest_version"])
        except KeyError:
            if not quiet:
                print(f" {Icon.ERROR} {__msg}")
                print(
                    f" {Icon.WARNING} "
                    + "Repository does not seem to indicate a compatible version"
                )
        else:
            if int(TBLOCK_VERSION.replace(".", "").split("-")[0]) < min_tblock_compat:
                if not quiet:
                    print(f" {Icon.ERROR} {__msg}")
                raise RepoError("index is not compatible with current tblock version")
            elif not quiet:
                print(f" {Icon.SUCCESS} {__msg}")
            if int(TBLOCK_VERSION.replace(".", "").split("-")[0]) < int(
                tblock_latest.replace(".", "")
            ):
                if not quiet:
                    print(
                        f" {Icon.INFORMATION} "
                        + "A new version of TBlock is available: {0}".format(
                            tblock_latest
                        )
                    )

        if not quiet:
            print(
                f" {Icon.INFORMATION} "
                + "Upgrading from version {0} to {1}".format(
                    current_repo_version, new_repo_version
                )
            )

        # Upgrade the repository
        total_filter_lists = len(data["filters"])
        count = 0
        all_filter_lists_in_new_index = []

        __msg = "Upgrading filter list index:"

        for _filter_list in data["filters"]:
            count += 1
            percent = int(count * 100 / total_filter_lists)
            if not quiet:
                print(
                    f" {loading_icon(count)} {__msg} {count}/{total_filter_lists} ({percent}%)",
                    end="\r",
                )

            metadata = {
                "title": None,
                "description": None,
                "homepage": None,
                "license": [],
                "tags": [],
                "warning": 0,
                "deprecated": False,
            }
            syntax = None
            mirrors = {}

            filter_obj = Filter(_filter_list)

            all_filter_lists_in_new_index.append(filter_obj.id)

            if filter_obj.exists and filter_obj.on_repo:
                source = filter_obj.source
            else:
                source = None

            if "title" in data["filters"][_filter_list].keys():
                metadata["title"] = data["filters"][_filter_list]["title"]
            if "desc" in data["filters"][_filter_list].keys():
                metadata["description"] = data["filters"][_filter_list]["desc"]
            if "homepage" in data["filters"][_filter_list].keys():
                metadata["homepage"] = data["filters"][_filter_list]["homepage"]
            if "license" in data["filters"][_filter_list].keys():
                metadata["license"] = data["filters"][_filter_list]["license"]
            if "syntax" in data["filters"][_filter_list].keys():
                syntax = data["filters"][_filter_list]["syntax"]
            if "source" in data["filters"][_filter_list].keys():
                source = data["filters"][_filter_list]["source"]
            if "mirrors" in data["filters"][_filter_list].keys():
                for m in data["filters"][_filter_list]["mirrors"]:
                    mirrors[m[0]] = {"compression": m[1]}
            if "tags" in data["filters"][_filter_list].keys():
                metadata["tags"] = data["filters"][_filter_list]["tags"]
            if "warning" in data["filters"][_filter_list].keys():
                metadata["warning"] = int(data["filters"][_filter_list]["warning"])
            if "deprecated" in data["filters"][_filter_list].keys():
                metadata["deprecated"] = data["filters"][_filter_list]["deprecated"]

            if filter_obj.exists and filter_obj.on_repo:
                try:
                    cursor.execute(
                        "UPDATE filters SET source=?, metadata=?, mirrors=?, syntax=? WHERE id=?;",
                        (
                            source,
                            json.dumps(metadata),
                            json.dumps(mirrors),
                            syntax,
                            filter_obj.id,
                        ),
                    )
                except sqlite3.IntegrityError:
                    if not quiet:
                        print(
                            f" {Icon.WARNING} Upstream filter list failed to sync because its source already exists: "
                            f"{_filter_list}"
                        )

            # If you are reading this, peace and love to you.
            # Be who you are and who you want to be. You are perfect.

            elif not filter_obj.exists:
                try:
                    cursor.execute(
                        "INSERT INTO filters (id, source, metadata, on_repo, subscribing, mirrors, syntax) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            filter_obj.id,
                            source,
                            json.dumps(metadata),
                            int(True),
                            int(False),
                            json.dumps(mirrors),
                            syntax,
                        ),
                    )
                except sqlite3.IntegrityError:
                    # That means the source is already taken
                    conflict_id = cursor.execute(
                        "SELECT id FROM filters WHERE source=?", (source,)
                    ).fetchone()[0]
                    if not quiet:
                        print(
                            f" {Icon.WARNING} Local filter list source conflicts with upstream: {conflict_id}"
                        )

            elif filter_obj.exists and not filter_obj.on_repo:
                if not quiet:
                    print(
                        f" {Icon.WARNING} Local filter list conflicts with upstream: {filter_obj.id}"
                    )

        # Check for all filter lists that were removed from the repository
        for filter_list in get_all_filter_lists(
            from_repo_only=True, subscribing_only=False
        ):
            if filter_list not in all_filter_lists_in_new_index:
                filter_obj = Filter(filter_list)
                if filter_obj.subscribing:
                    # Transform the filter into a custom filter if the user is subscribing to it
                    db.cursor().execute(
                        "UPDATE filters SET on_repo=? WHERE id=?;",
                        (int(False), filter_obj.id),
                    )
                else:
                    # Delete the filter if the user is not subscribing to it
                    db.cursor().execute(
                        "DELETE FROM filters WHERE id=?", (filter_obj.id,)
                    )

        # Change the version of the filter list repository in the database
        if current_repo_version == 0:
            cursor.execute(
                'INSERT INTO system (variable, value) VALUES ("repo_version", ?);',
                (new_repo_version,),
            )
        else:
            cursor.execute(
                'UPDATE system SET value=? WHERE variable="repo_version";',
                (new_repo_version,),
            )

        db.commit()
        db.close()
        if not quiet:
            print(f" {Icon.SUCCESS} {__msg} {count}/{total_filter_lists} (100%)")

        # Unlock the database
        if lock_database:
            unlock_db()


def setup_profile(profile: tuple, quiet: bool = False) -> None:
    subscribe(list(profile), do_not_prompt=True, quiet=quiet, sync_repo=True)


def init_tblock() -> None:
    # Check root access
    if not check_root_access():
        raise PermissionError("you need to run as root to perform this operation")

    print(
        f"\n{Font.BOLD}> Welcome to TBlock!{Font.DEFAULT}\n\n\n"
        ":: Please select the level that suits your needs the best:"
        "\n\n [0] None: lets you configure everything yourself\n"
        " [1] Light: light protection, some ads and trackers won't be blocked\n"
        " [2] Balanced: perfect solution for regular users\n"
        " [3] Aggressive: powerful, yet it may break some web pages\n"
    )
    choice = None
    while choice is None:
        answer = input("Your choice [default=2]: ")
        if answer == "0":
            choice = Profile.NONE
        elif answer == "1":
            choice = Profile.LIGHT
        elif answer == "2" or answer == "":
            choice = Profile.BALANCED
        elif answer == "3":
            choice = Profile.AGGRESSIVE
        else:
            choice = None
    else:
        if get_user_response("Block malicious websites?"):
            choice += Components.SECURITY
        if get_user_response("Block pornographic websites?"):
            choice += Components.PORNOGRAPHY
        if get_user_response("Block websites that spread fake news?"):
            choice += Components.FAKE_NEWS
        if get_user_response("Block websites related to addictive substances?"):
            choice += Components.DRUGS
        if get_user_response("Block gambling websites?"):
            choice += Components.GAMBLING
        if get_user_response("Block illegal websites (piracy)?"):
            choice += Components.PIRACY
        if get_user_response("Block cryptocurrency services?"):
            choice += Components.CRYPTO
        if get_user_response("Block hate speech and far-right content?"):
            # fuck nazis 0w0
            choice += Components.HATE
        print("\n")
        try:
            setup_profile(tuple(choice))
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        print(
            f"\n{Font.BOLD}> Wonderful! TBlock is now protecting you!{Font.DEFAULT}\n\n"
            f"To disable it, simply run:\n    $ {Fore.GREEN}tblock{Style.RESET_ALL} -D"
            f"\nAnd then, to enable it again:\n    $ {Fore.GREEN}tblock{Style.RESET_ALL} -E\n"
            f"It is also highly recommended to read the documentation: "
            f"https://docs.tblock.me"
        )
        print(
            f"\n{Font.BOLD}> The setup is now finished{Font.DEFAULT}.\nHit ENTER to exit the program."
        )
        input()

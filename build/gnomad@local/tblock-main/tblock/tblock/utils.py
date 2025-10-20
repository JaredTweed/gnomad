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

# External modules
import hashlib

import requests
import urllib3
import urllib3.exceptions
import ipaddress

# Standard modules
import re
import os
import os.path
import shutil

# Local modules
from .style import Icon, loading_icon
from .exceptions import TBlockNetworkError, DatabaseLockedError
from .config import Path
from .const import USER_AGENT


def db_is_locked() -> bool:
    return os.path.isfile(Path.DB_LOCK)


def lock_db() -> None:
    if db_is_locked():
        raise DatabaseLockedError(
            f"database is locked, please wait for other processes to terminate.\nIf you are sure "
            f"that the daemon or any other instances are not running, you can delete:\n"
            f"-> {Path.DB_LOCK}"
        )
    else:
        with open(Path.DB_LOCK, "wt") as w:
            w.write(str(os.getpid()))


def unlock_db() -> None:
    if db_is_locked():
        try:
            with open(Path.DB_LOCK, "rt") as r:
                pid = int(r.read())
            if pid == os.getpid():
                os.remove(Path.DB_LOCK)
        except FileNotFoundError:
            pass


def get_user_response(message, strict: bool = True) -> bool:
    answer = input(message + " [y/n] ")
    while ("n" != answer.lower() != "y") and (answer != "" or strict):
        answer = input(message + " [y/n] ")
    else:
        return answer.lower() == "y" or (answer == "" and not strict)


def _get_user_consent() -> bool:
    return get_user_response(":: Are you sure to continue ?", strict=False)


def is_valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return False
    return True


def is_valid_domain(domain: str, allow_wildcards: bool = False) -> bool:
    if domain in ("localhost", "localhost.localdomain", "0.0.0.0"):
        return False
    if re.match(r"^[*]+$", domain):
        return False
    if re.findall(r"[/+\\_%?!=:,;<>\[\]$()\"]", domain):
        return False
    if domain.__contains__("*") and not allow_wildcards:
        return False
    return True


def contains_wildcards(domain) -> bool:
    if re.findall(r"[/+\\_%?!=:,;<>\[\]$()\"]", domain):
        return False
    if domain.__contains__("*"):
        return True
    return False


def owner_is_root(filename: str) -> bool:
    return os.getuid() == os.stat(filename).st_uid


def prompt_user(message: str, list_of_elements: list = None) -> bool:
    """Prompt the user before executing an action
    Args:
        message (str): The message to display
        list_of_elements (list, optional): A list of elements to display
    """
    output_string = ""
    line_count = 0
    if list_of_elements:
        for item in list_of_elements:
            if line_count + len(f" {item}") >= 62:
                output_string += f"\n  {item}"
                line_count = len(f" {item}")
            else:
                output_string += f" {item}"
                line_count += len(f" {item}")
    print(f":: {message}")
    if output_string:
        print(f"\n {output_string}\n")
    try:
        answer = _get_user_consent()
    except KeyboardInterrupt:
        return False
    else:
        return answer


def get_readable_size(bytes_length: float) -> str:
    """
    Get human-readable size of a file
    :param bytes_length: The file size (in Bytes)
    :return: A human-readable format of the file size
    """
    for unity in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if bytes_length < 1024.0:
            return f"{round(bytes_length, 1)} {unity}"
        else:
            bytes_length /= 1024.0


def is_url(string: str) -> bool:
    """
    Check if a string is a valid web URL
    :param string: The string to check
    :return: True if string is a valid URL
    """
    return bool(re.match(r"(http(s|)|(s|)ftp)://", string))


def fetch_file(
    location: str,
    description: str,
    output_file: str,
    quiet: bool = False,
    sha512sum: str = None,
) -> bool:
    """
    Download or copy a file from the internet or a local directory and display a pretty animation to show progress
    :param location: Web location of the file to download
    :param description: Title of the file that is being downloaded
    :param output_file: Where to write the downloaded file
    :param quiet: Optional. Do not display an output (false by default)
    :param sha512sum: Optional. Compare the hash of the file with the one given here. Raise an error if it doesn't match
    :return: True if file has been downloaded successfully.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": ""
    }
    __msg = "Fetching {0}".format(description)
    if is_url(location):
        # File is online and needs to be downloaded
        try:
            response = requests.get(location, stream=True, headers=headers, timeout=8)
            if response.status_code != 200:
                raise TBlockNetworkError("status code is not 200")
            online_size = int(response.headers.get("content-length", 0))
            online_size_readable = get_readable_size(online_size)

            local_size = 0
            count = 0

            with open(output_file, "wb") as f:
                for data in response.iter_content(1024):
                    count += 1
                    local_size += 1024
                    if online_size != 0:
                        percent = int(local_size * 100 / online_size)
                    else:
                        percent = "- "
                    if not quiet:
                        print(
                            f" {loading_icon(count)} {__msg} ({online_size_readable}): {percent}%",
                            end="\r",
                        )
                    f.write(data)

            with open(output_file, "rb") as f:
                local_size = len(f.read())
            if not quiet:
                print(
                    f" {Icon.SUCCESS} {__msg} ({get_readable_size(local_size)}): 100%"
                )
            if sha512sum is not None:
                if not quiet:
                    print(f" {loading_icon(1)} Checking hash", end="\r")
                with open(output_file, "rb") as r:
                    hash = hashlib.sha512(r.read()).hexdigest()
                if hash == sha512sum:
                    if not quiet:
                        print(f" {Icon.SUCCESS} Checking hash")
                    return True
                else:
                    if not quiet:
                        print(f" {Icon.ERROR} Checking hash")
                    return False
            else:
                return True

        except (
            requests.exceptions.ConnectionError,
            urllib3.exceptions.MaxRetryError,
            ConnectionRefusedError,
            urllib3.exceptions.NewConnectionError,
            TBlockNetworkError,
            requests.exceptions.ReadTimeout,
        ):
            if not quiet:
                print(f" {Icon.ERROR} {__msg} (0 B): 0%")
            return False
    else:
        try:
            # File is local and needs to be copied
            with open(location, "rb") as f:
                online_size = len(f.read())
            online_size_readable = get_readable_size(online_size)
            if not quiet:
                print(
                    f" {loading_icon(1)} {__msg} ({online_size_readable}): 0%", end="\r"
                )
            shutil.copy(location, output_file, follow_symlinks=True)
            if not quiet:
                print(f" {Icon.SUCCESS} {__msg} ({online_size_readable}): 100%")
            if sha512sum is not None:
                if not quiet:
                    print(f" {loading_icon(1)} Checking hash", end="\r")
                with open(output_file, "rb") as r:
                    hash = hashlib.sha512(r.read()).hexdigest()
                if hash == sha512sum:
                    if not quiet:
                        print(f" {Icon.SUCCESS} Checking hash")
                    return True
                else:
                    if not quiet:
                        print(f" {Icon.ERROR} Checking hash")
                    return False
            else:
                return True
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            if not quiet:
                print(f" {Icon.ERROR} {__msg} (0 B): 0%")
            return False


def check_root_access() -> bool:
    """
    Check whether the program is running with root access or not

    :return: bool
    """
    try:
        with open(Path.HOSTS, "at") as t:
            t.close()
    except (OSError, PermissionError):
        return False
    else:
        return True


def get_db_size() -> int:
    return os.path.getsize(Path.DATABASE)

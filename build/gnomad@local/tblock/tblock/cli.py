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
import sqlite3
import sys

# Local modules
from .config import log_message, create_dirs, VERSION, Path
from .filters import (
    subscribe,
    subscribe_custom,
    update_all,
    unsubscribe,
    rename_custom,
    sync_filter_list_repo,
    show_info,
    list_filter_lists,
    search_filter_lists,
    purge_cache,
    query_domain_to_filter_list,
    init_tblock,
)
from .hosts import update_hosts, restore_hosts, gen_hosts, enable_protection
from .style import show_status
from tblock.daemon import start_daemon
from .argumentor import Arguments
from .rules import (
    allow_domains,
    block_domains,
    redirect_domains,
    delete_rules,
    list_rules,
)
from .exceptions import (
    RuleError,
    TBlockNetworkError,
    HostsError,
    FilterError,
    FilterSyntaxError,
    RepoError,
    TBlockError,
    DatabaseLockedError,
)
from .compat import init_db
from .converter import convert, detect_filter_list_syntax, list_syntax
from .utils import check_root_access, unlock_db

# External modules
from colorama import Fore, Style


LICENSE_TEXT = """This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>."""


def __setup_args_tblock(args: list) -> Arguments:
    """
    Set up the argument parser for the ad-blocker

    :param args: The command-line arguments
    """
    parser = Arguments(
        arguments=args,
        exec_name="tblock",
        copyright_header="TBlock - An anti-capitalist ad-blocker that uses the hosts file\n"
        "Copyright (C) 2021-2025 Camelia Lavender <camelia@tblock.me>\n",
        more_info_footer="For more information, see tblock(1).",
    )

    # Add operation groups
    parser.add_operation_group("General", "General")
    parser.add_operation_group("Hosts", "Hosts")
    parser.add_operation_group("Rules", "Rules")
    parser.add_operation_group("Filter lists", "Filter lists")
    parser.add_operation_group("Search", "Search")

    # Add option groups
    parser.add_option_group("General", "General")
    parser.add_option_group("Rules", "Rules")
    parser.add_option_group("Filter lists", "Filter lists")
    parser.add_option_group("Search", "Search")

    # Add "General" operations
    parser.add_operation(
        operation="--init",
        short_operation="-1",
        value_type=bool,
        description="Setup TBlock for the first time",
        group="General",
    )
    parser.add_operation(
        operation="--help",
        short_operation="-h",
        value_type=bool,
        description="Show this help page",
        group="General",
    )
    parser.add_operation(
        operation="--gen-hosts",
        short_operation="-G",
        value_type=bool,
        description="Generate hosts file template",
        group="General",
    )
    parser.add_operation(
        operation="--status",
        short_operation="-s",
        value_type=bool,
        description="Show status information",
        group="General",
    )
    parser.add_operation(
        operation="--version",
        short_operation="-v",
        value_type=bool,
        description="Show version and license information",
        group="General",
    )

    # Add "Hosts" operations
    parser.add_operation(
        operation="--build",
        short_operation="-B",
        value_type=bool,
        description="Rebuild hosts file",
        group="Hosts",
    )
    parser.add_operation(
        operation="--disable",
        short_operation="-D",
        value_type=bool,
        description="Disable TBlock",
        group="Hosts",
    )
    parser.add_operation(
        operation="--enable",
        short_operation="-E",
        value_type=bool,
        description="Enable TBlock",
        group="Hosts",
    )
    parser.add_operation(
        operation="--update-hosts",
        short_operation="-H",
        value_type=bool,
        description="Rebuild hosts file (deprecated)",
        group="Hosts",
        hidden=True,
    )

    # Add "Rules" operations
    parser.add_operation(
        operation="--allow",
        short_operation="-a",
        value_type=list,
        description="Allow specified domain(s)",
        group="Rules",
    )
    parser.add_operation(
        operation="--block",
        short_operation="-b",
        value_type=list,
        description="Block specified domain(s)",
        group="Rules",
    )
    parser.add_operation(
        operation="--redirect",
        short_operation="-r",
        value_type=list,
        description="Redirect specified domain(s)",
        group="Rules",
    )
    parser.add_operation(
        operation="--delete-rule",
        short_operation="-d",
        value_type=list,
        description="Delete rule(s) for specified domain(s)",
        group="Rules",
    )

    # Add "Filter lists" operations
    parser.add_operation(
        operation="--sync",
        short_operation="-Y",
        value_type=bool,
        description="Sync the filter list repository",
        group="Filter lists",
    )
    parser.add_operation(
        operation="--subscribe",
        short_operation="-S",
        value_type=list,
        description="Subscribe to specified filter list(s)",
        group="Filter lists",
    )
    parser.add_operation(
        operation="--add-custom",
        short_operation="-C",
        value_type=list,
        description="Subscribe to specified custom filter list(s)",
        group="Filter lists",
    )
    parser.add_operation(
        operation="--rename",
        short_operation="-N",
        value_type=list,
        description="Rename specified custom filter list(s)",
        group="Filter lists",
    )
    parser.add_operation(
        operation="--remove",
        short_operation="-R",
        value_type=list,
        description="Unsubscribe from specified filter list(s)",
        group="Filter lists",
    )
    parser.add_operation(
        operation="--update",
        short_operation="-U",
        value_type=bool,
        description="Update all filter lists",
        group="Filter lists",
    )
    parser.add_operation(
        operation="--info",
        short_operation="-I",
        value_type=list,
        description="Get information about specified filter list(s)",
        group="Filter lists",
    )
    # Only kept for compatibility purposes
    parser.add_operation(
        operation="--mod",
        short_operation="-M",
        value_type=list,
        description="Change permissions of specified filter list(s) (deprecated)",
        group="Filter lists",
        hidden=True,
    )
    parser.add_operation(
        operation="--purge-cache",
        short_operation="-P",
        value_type=bool,
        description="Remove cached filter lists (deprecated)",
        group="Filter lists",
        hidden=True,
    )

    # Add "Search" operations
    parser.add_operation(
        operation="--list-rules",
        short_operation="-l",
        value_type=bool,
        description="List rules",
        group="Search",
    )
    parser.add_operation(
        operation="--list",
        short_operation="-L",
        value_type=bool,
        description="List filter lists",
        group="Search",
    )
    parser.add_operation(
        operation="--search",
        short_operation="-Q",
        value_type=str,
        description="Perform a search inside filter lists database",
        group="Search",
    )
    parser.add_operation(
        operation="--which",
        short_operation="-W",
        value_type=list,
        description="Find which filter list is managing specified domain(s)",
        group="Search",
    )

    # Add "General" options
    parser.add_option(
        option="--no-prompt",
        short_option="-n",
        value_type=bool,
        description="Do not prompt for anything",
        group="General",
        available_with_groups=["General", "Rules", "Filter lists", "Hosts"],
    )
    parser.add_option(
        option="--quiet",
        short_option="-q",
        value_type=bool,
        description="Be the least verbose possible",
        group="General",
        available_with_groups=["General", "Rules", "Filter lists", "Hosts", "Search"],
    )

    # Add "Rules" options
    parser.add_option(
        option="--ip",
        short_option="-i",
        value_type=str,
        description="Specify the redirection IP address (with --redirect)",
        group="Rules",
        available_with_operations=["--redirect"],
        required_by_operations=["--redirect"],
    )

    # Add "Filter lists" options
    parser.add_option(
        option="--with-sync",
        short_option="-y",
        value_type=bool,
        description="Also sync filter list repository",
        group="Filter lists",
        available_with_operations=[
            "--subscribe",
            "--add-custom",
            "--rename",
            "--remove",
            "--update",
            "--update-all",
            "--mod",
        ],
    )
    parser.add_option(
        option="--with-update",
        short_option="-u",
        value_type=bool,
        description="Also update all filter lists",
        group="Filter lists",
        available_with_operations=[
            "--subscribe",
            "--add-custom",
            "--rename",
            "--remove",
            "--mod",
        ],
    )
    parser.add_option(
        option="--custom-syntax",
        short_option="-x",
        value_type=str,
        description="Specify the syntax of a custom filter list",
        group="Filter lists",
        available_with_operations=["--add-custom"],
    )
    parser.add_option(
        option="--force",
        short_option="-f",
        value_type=bool,
        description="Force to update filter lists or repository",
        group="Filter lists",
        available_with_operations=[
            "--sync",
            "--subscribe",
            "--remove",
            "--update",
            "--update-all",
        ],
    )
    # Only kept for compatibility purposes
    parser.add_option(
        option="--permissions",
        short_option="-p",
        value_type=str,
        description="Specify the permissions to give to filter lists (deprecated)",
        group="Filter lists",
        available_with_operations=["--subscribe", "--add-custom", "--mod"],
        hidden=True,
    )

    # Add "Search" options
    parser.add_option(
        option="--user",
        short_option="-e",
        value_type=bool,
        description="List user rules only",
        group="Search",
        available_with_operations=["--list-rules"],
    )
    parser.add_option(
        option="--standard",
        short_option="-t",
        value_type=bool,
        description="List standard (filter lists) rules only",
        group="Search",
        available_with_operations=["--list-rules"],
    )
    parser.add_option(
        option="--from-filters",
        short_option="-m",
        value_type=list,
        description="List rules coming from specific filter lists only",
        group="Search",
        available_with_operations=["--list-rules"],
    )
    parser.add_option(
        option="--custom",
        short_option="-c",
        value_type=bool,
        description="List custom filter lists only",
        group="Search",
        available_with_operations=["--list", "--search"],
    )
    parser.add_option(
        option="--on-repo",
        short_option="-w",
        value_type=bool,
        description="List filter lists available on the filter list repository only",
        group="Search",
        available_with_operations=["--list", "--search"],
    )
    parser.add_option(
        option="--subscribing",
        short_option="-k",
        value_type=bool,
        description="List subscribed filter lists only",
        group="Search",
        available_with_operations=["--list", "--search"],
    )
    parser.add_option(
        option="--not-subscribing",
        short_option="-z",
        value_type=bool,
        description="List unsubscribed filter lists only",
        group="Search",
        available_with_operations=["--list", "--search"],
    )

    return parser


def __setup_args_tblockc(args: list) -> Arguments:
    """
    Set up the argument parser for the converter

    :param args: The command-line arguments
    """
    parser = Arguments(
        arguments=args,
        exec_name="tblockc",
        copyright_header="TBlockc - TBlock's built-in filter converter\n"
        "Copyright (C) 2021-2025 Camelia Lavender <camelia@tblock.me>\n",
        more_info_footer="For more information, see tblockc(1).",
    )

    # Add operations
    parser.add_operation(
        operation="--help",
        short_operation="-h",
        value_type=bool,
        description="Show this help page",
    )
    parser.add_operation(
        operation="--version",
        short_operation="-v",
        value_type=bool,
        description="Show version and license information",
    )
    parser.add_operation(
        operation="--get-syntax",
        short_operation="-g",
        value_type=str,
        description="Detect the filter list format of a file",
    )
    parser.add_operation(
        operation="--list-syntax",
        short_operation="-l",
        value_type=bool,
        description="List supported filter formats",
    )
    parser.add_operation(
        operation="--convert",
        short_operation="-C",
        value_type=str,
        description="Convert a filter list into another filter list format",
    )

    # Add options
    parser.add_option(
        option="--syntax",
        short_option="-s",
        value_type=str,
        description="Specify the syntax to use for output",
        required_by_operations=["--convert"],
        available_with_operations=["--convert"],
    )
    parser.add_option(
        option="--output",
        short_option="-o",
        value_type=str,
        description="Specify the output file",
        required_by_operations=["--convert"],
        available_with_operations=["--convert"],
    )
    parser.add_option(
        option="--comments",
        short_option="-c",
        value_type=bool,
        description="Also convert comments",
        available_with_operations=["--convert"],
    )
    parser.add_option(
        option="--input-syntax",
        short_option="-i",
        value_type=str,
        description="Specify the input filter list format",
        available_with_operations=["--convert"],
    )
    parser.add_option(
        option="--zero",
        short_option="-0",
        value_type=bool,
        description="Redirect domains to 0.0.0.0 instead of 127.0.0.1 (hosts/dnsmasq)",
        available_with_operations=["--convert"],
    )
    parser.add_option(
        option="--optimize",
        short_option="-z",
        value_type=bool,
        description="Do not convert blank lines",
        available_with_operations=["--convert"],
    )
    parser.add_option(
        option="--server",
        short_option="-e",
        value_type=bool,
        description='Block domains using "server" (dnsmasq)',
        available_with_operations=["--convert"],
    )
    parser.add_option(
        option="--quiet",
        short_option="-q",
        value_type=bool,
        description="Be the least verbose possible",
        available_with_operations=["--convert", "--get-syntax"],
    )

    return parser


def __setup_args_tblockd(args: list) -> Arguments:
    """
    Set up the argument parser for the daemon

    :param args: The command-line arguments
    """

    parser = Arguments(
        arguments=args,
        exec_name="tblockd",
        copyright_header="TBlockD - TBlock's built-in daemon\nCopyright (C) 2021-2025 Camelia Lavender <camelia@tblock.me>\n",
        more_info_footer="For more information, see tblockd(1).",
    )

    parser.add_operation(
        operation="--daemon",
        short_operation="-d",
        value_type=bool,
        description="Start the daemon",
    )
    parser.add_operation(
        operation="--help",
        short_operation="-h",
        value_type=bool,
        description="Show this help page",
    )
    parser.add_operation(
        operation="--version",
        short_operation="-v",
        value_type=bool,
        description="Show version and license information",
    )
    parser.add_option(
        option="--config",
        short_option="-c",
        value_type=str,
        available_with_operations=["--daemon"],
        description="Path to the config file to use",
        default_value=Path.CONFIG,
    )
    parser.add_option(
        option="--quiet",
        short_option="-q",
        value_type=bool,
        available_with_operations=["--daemon"],
        description="Do not print output",
    )
    parser.add_option(
        option="--no-pid",
        short_option="-n",
        value_type=bool,
        available_with_operations=["--daemon"],
        description="Do not create a PID file",
    )

    return parser


def __parse_args_tblock(args: list) -> None:
    """
    Parse arguments and start functions of the ad-blocker

    :param args: The command-line arguments
    """

    parser = __setup_args_tblock(args)

    # Parse arguments
    operations, options = parser.parse()

    if operations["--help"]:
        print(parser.help_page)
    elif operations["--status"]:
        show_status(quiet=options["--quiet"])
    elif operations["--version"]:
        print(
            f"TBlock v{VERSION} - An anti-capitalist ad-blocker that uses the hosts file\n\n{LICENSE_TEXT}"
        )
    elif operations["--allow"]:
        allow_domains(
            domains=operations["--allow"],
            force=options["--force"],
            quiet=options["--quiet"],
            do_not_prompt=options["--no-prompt"],
        )
    elif operations["--block"]:
        block_domains(
            domains=operations["--block"],
            force=options["--force"],
            quiet=options["--quiet"],
            do_not_prompt=options["--no-prompt"],
        )
    elif operations["--redirect"]:
        redirect_domains(
            domains=operations["--redirect"],
            ip=options["--ip"],
            force=options["--force"],
            quiet=options["--quiet"],
            do_not_prompt=options["--no-prompt"],
        )
    elif operations["--delete-rule"]:
        delete_rules(
            domains=operations["--delete-rule"],
            quiet=options["--quiet"],
            do_not_prompt=options["--no-prompt"],
        )
    elif operations["--init"]:
        init_tblock()
    elif operations["--sync"]:
        sync_filter_list_repo(force=options["--force"], quiet=options["--quiet"])
    elif operations["--subscribe"]:
        if options["--permissions"]:
            print(
                Fore.YELLOW
                + "Warning: option --permissions is deprecated and no longer does anything since permissions do not exist anymore."
                + Style.RESET_ALL
            )
        subscribe(
            filter_lists=operations["--subscribe"],
            do_not_prompt=options["--no-prompt"],
            quiet=options["--quiet"],
            sync_repo=options["--with-sync"],
            full_update=options["--with-update"],
            force=options["--force"],
        )
    elif operations["--add-custom"]:
        if options["--permissions"]:
            print(
                Fore.YELLOW
                + "Warning: option --permissions is deprecated and no longer does anything since permissions do not exist anymore."
                + Style.RESET_ALL
            )
        subscribe_custom(
            filter_lists=operations["--add-custom"],
            do_not_prompt=options["--no-prompt"],
            quiet=options["--quiet"],
            sync_repo=options["--with-sync"],
            full_update=options["--with-update"],
            force=options["--force"],
            custom_syntax=options["--custom-syntax"],
        )
    elif operations["--rename"]:
        rename_custom(
            filter_lists=operations["--rename"],
            do_not_prompt=options["--no-prompt"],
            quiet=options["--quiet"],
            sync_repo=options["--with-sync"],
            full_update=options["--with-update"],
            force=options["--force"],
        )
    elif operations["--remove"]:
        unsubscribe(
            filter_lists=operations["--remove"],
            do_not_prompt=options["--no-prompt"],
            quiet=options["--quiet"],
            sync_repo=options["--with-sync"],
            full_update=options["--with-update"],
            force=options["--force"],
        )
    elif operations["--update"]:
        update_all(
            do_not_prompt=options["--no-prompt"],
            quiet=options["--quiet"],
            sync_repo=options["--with-sync"],
            force=options["--force"],
        )
    elif operations["--mod"]:
        print(
            Fore.YELLOW
            + "Warning: operation --mod is deprecated and no longer does anything since permissions do not exist anymore."
            + Style.RESET_ALL
        )
    elif operations["--info"]:
        show_info(filter_lists=operations["--info"], quiet=options["--quiet"])
    elif operations["--purge-cache"]:
        print(
            Fore.YELLOW
            + "Warning: operation --purge-cache is deprecated. Please use your shell instead."
            + Style.RESET_ALL
        )
        purge_cache(do_not_prompt=options["--no-prompt"], quiet=options["--quiet"])
    elif operations["--disable"]:
        restore_hosts(quiet=options["--quiet"], do_not_prompt=options["--no-prompt"])
    elif operations["--enable"]:
        enable_protection(
            quiet=options["--quiet"], do_not_prompt=options["--no-prompt"]
        )
    elif operations["--build"]:
        update_hosts(quiet=options["--quiet"], do_not_prompt=options["--no-prompt"])
    elif operations["--update-hosts"]:
        print(
            Fore.YELLOW
            + "Warning: operation --update-hosts is deprecated. Please use --build instead."
            + Style.RESET_ALL
        )
        update_hosts(quiet=options["--quiet"], do_not_prompt=options["--no-prompt"])
    elif operations["--gen-hosts"]:
        gen_hosts()
    elif operations["--list-rules"]:
        list_rules(
            from_filter_lists=options["--from-filters"],
            user_only=options["--user"],
            standard_only=options["--standard"],
            quiet=options["--quiet"],
        )
    elif operations["--list"]:
        list_filter_lists(
            custom_only=options["--custom"],
            on_repo_only=options["--on-repo"],
            subscribing_only=options["--subscribing"],
            not_subscribing_only=options["--not-subscribing"],
            quiet=options["--quiet"],
        )
    elif operations["--search"]:
        search_filter_lists(
            query=operations["--search"],
            custom_only=options["--custom"],
            on_repo_only=options["--on-repo"],
            subscribing_only=options["--subscribing"],
            not_subscribing_only=options["--not-subscribing"],
            quiet=options["--quiet"],
        )
    elif operations["--which"]:
        query_domain_to_filter_list(
            domains=operations["--which"], quiet=options["--quiet"]
        )


def __parse_args_tblockc(args: list) -> None:
    """
    Parse arguments and start functions of the daemon

    :param args: The command-line arguments
    """

    parser = __setup_args_tblockc(args)

    # Parse arguments
    operations, options = parser.parse()
    if operations["--help"]:
        print(parser.help_page)
    elif operations["--version"]:
        print(
            f"""TBlockc v{VERSION} - TBlock's built-in filter converter\n\n{LICENSE_TEXT}"""
            ""
        )
    elif operations["--get-syntax"]:
        detect_filter_list_syntax(operations["--get-syntax"], quiet=options["--quiet"])
    elif operations["--list-syntax"]:
        list_syntax()
    elif operations["--convert"]:
        convert(
            input_file=operations["--convert"],
            output_file=options["--output"],
            output_syntax=options["--syntax"],
            input_syntax=options["--input-syntax"],
            allow_comments=options["--comments"],
            redirect_to_zero=options["--zero"],
            dnsmasq_server=options["--server"],
            optimize=options["--optimize"],
            quiet=options["--quiet"],
        )


def __parse_args_tblockd(args: list) -> None:
    """
    Parse arguments and start functions of the daemon

    :param args: The command-line arguments
    """

    parser = __setup_args_tblockd(args)

    # Parse arguments
    operations, options = parser.parse()
    if operations["--daemon"] and options["--config"]:
        start_daemon(
            options["--config"], no_pid=options["--no-pid"], quiet=options["--quiet"]
        )
    elif operations["--help"]:
        print(parser.help_page)
    elif operations["--version"]:
        print(f"""TBlockD v{VERSION} - TBlock's built-in daemon\n\n{LICENSE_TEXT}""")


def run(args: list = None) -> None:
    """
    Start the CLI ad-blocker
    """
    if args is None:
        args = sys.argv[1:]
    try:
        log_message(f"[tblock]  INFO:  running: {args.__str__()}")
    except PermissionError:
        pass
    else:
        create_dirs()
        try:
            if check_root_access():
                init_db()
        except sqlite3.OperationalError as err:
            log_message(
                f"[core]    ERROR: database operation failed with error: {0}".format(
                    err.__str__()
                )
            )
    try:
        __parse_args_tblock(args)
    except (DatabaseLockedError, sqlite3.OperationalError) as err:
        print(Fore.YELLOW + "Error: {0}".format(err.__str__()) + Style.RESET_ALL)
        raise SystemExit(1)
    except (
        RuleError,
        TBlockNetworkError,
        HostsError,
        FilterError,
        FilterSyntaxError,
        RepoError,
        PermissionError,
        TBlockError,
        FileNotFoundError,
    ) as err:
        log_message(
            f"[tblock]  ERROR: caught {type(err.__class__()).__name__}: {err.__str__()}"
        )
        print(Fore.RED + "Error: {0}".format(err.__str__()) + Style.RESET_ALL)
        if check_root_access():
            unlock_db()
        raise SystemExit(1)
    except KeyboardInterrupt:
        log_message("[tblock]  ERROR: caught KeyboardInterrupt: terminated by user")
        if check_root_access():
            unlock_db()
        raise SystemExit(1)
    else:
        log_message("[tblock]  DONE:  operation was successful")


def run_converter(args: list = None) -> None:
    """
    Start the CLI ad-blocker
    """
    if args is None:
        args = sys.argv[1:]
    try:
        __parse_args_tblockc(args)
    except (
        FilterSyntaxError,
        RepoError,
        PermissionError,
        FileNotFoundError,
        TBlockError,
    ) as err:
        print(Fore.RED + "Error: {0}".format(err.__str__()) + Style.RESET_ALL)
        raise SystemExit(1)
    except KeyboardInterrupt:
        raise SystemExit(1)


def run_daemon(args: list = None) -> None:
    """
    Start the CLI daemon
    """
    if args is None:
        args = sys.argv[1:]
    try:
        log_message(f"[tblockd] INFO:  running: {args.__str__()}")
    except PermissionError:
        pass
    else:
        create_dirs()
        try:
            if check_root_access():
                init_db()
        except sqlite3.OperationalError as err:
            log_message(
                "[core]    ERROR: database operation failed with error: {0}".format(
                    err.__str__()
                )
            )
    try:
        __parse_args_tblockd(args)
    except DatabaseLockedError as err:
        print(Fore.YELLOW + "Error: {0}".format(err.__str__()) + Style.RESET_ALL)
        raise SystemExit(1)
    except (
        RuleError,
        TBlockNetworkError,
        HostsError,
        FilterError,
        FilterSyntaxError,
        RepoError,
        PermissionError,
        TBlockError,
        FileNotFoundError,
    ) as err:
        log_message(
            f"[tblockd] ERROR: caught {type(err.__class__()).__name__}: {err.__str__()}"
        )
        print(Fore.RED + "Error: {0}".format(err.__str__()) + Style.RESET_ALL)
        if check_root_access():
            unlock_db()
        raise SystemExit(1)
    except KeyboardInterrupt:
        log_message("[tblockd] ERROR: caught KeyboardInterrupt: terminated by user")
        if check_root_access():
            unlock_db()
        raise SystemExit(1)
    finally:
        if check_root_access():
            unlock_db()
        log_message("[tblockd] INFO:  daemon was stopped")

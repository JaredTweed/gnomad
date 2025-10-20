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

from .config import VERSION, Var
from .config import hosts_are_safe, Path
from .filters import (
    subscribe,
    subscribe_custom,
    update,
    update_all,
    rename_custom,
    change_permissions,
    sync_filter_list_repo,
    get_all_filter_lists,
    unsubscribe,
    Filter,
    purge_cache,
    get_active_filter_lists_count,
    get_search_results_filter_lists,
)
from .rules import (
    allow_domains,
    block_domains,
    redirect_domains,
    delete_rules,
    Rule,
    get_all_rules,
    get_rules_count,
)
from .const import RulePolicy, USER_RULE_PRIORITY, FilterPermissions, FilterSyntax
from .hosts import update_hosts, restore_hosts, enable_protection
from tblock.daemon import start_daemon

# This step is required. Otherwise, if using:
# from .config import VERSION as __version__
# the tests will return an error, because a constant is imported as a non-constant
__version__ = VERSION
del VERSION

# Specify other metadata
__url__ = "https://tblock.codeberg.page"
__license__ = "GPLv3"

# Simplify rule policies
ALLOW = RulePolicy.ALLOW
BLOCK = RulePolicy.BLOCK
REDIRECT = RulePolicy.REDIRECT
del RulePolicy

# Simplify config variables
DEFAULT_IP = Var.DEFAULT_IP
REPO_MIRRORS = Var.REPO_MIRRORS
ALLOW_IPV6 = Var.ALLOW_IPV6
DEFAULT_IPV6 = Var.DEFAULT_IPV6
del Var

# This doesn't do anything, it is just kept here for compatibility purposes
DEFAULT_PERMISSIONS = FilterPermissions("AB")
DEFAULT_PERMISSIONS_CUSTOM = FilterPermissions("AB")

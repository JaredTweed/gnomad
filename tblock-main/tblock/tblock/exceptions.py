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


class TBlockError(IOError):
    def __init__(self, *args):
        super(TBlockError, self).__init__(*args)


class ErrorsOccurredError(TBlockError):
    def __init__(self, *args):
        super(ErrorsOccurredError, self).__init__(*args)


class TBlockNetworkError(TBlockError):
    def __init__(self, *args):
        super(TBlockNetworkError, self).__init__(*args)


class RuleError(TBlockError):
    def __init__(self, *args):
        super(RuleError, self).__init__(*args)


class FilterError(TBlockError):
    def __init__(self, *args):
        super(FilterError, self).__init__(*args)


class RepoError(TBlockError):
    def __init__(self, *args):
        super(RepoError, self).__init__(*args)


class HostsError(TBlockError):
    def __init__(self, *args):
        super(HostsError, self).__init__(*args)


class FilterSyntaxError(TBlockError):
    def __init__(self, *args):
        super(FilterSyntaxError, self).__init__(*args)


class DatabaseLockedError(TBlockError):
    def __init__(self, *args):
        super(DatabaseLockedError, self).__init__(*args)

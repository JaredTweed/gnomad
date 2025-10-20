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


class FilterPermissions:
    """
    Filter list permissions object
    """

    def __init__(self, permissions: str) -> None:
        try:
            self.ALLOW = bool(re.findall(re.compile(r"a", re.IGNORECASE), permissions))
            self.BLOCK = bool(re.findall(re.compile(r"b", re.IGNORECASE), permissions))
            self.REDIRECT = bool(
                re.findall(re.compile(r"r", re.IGNORECASE), permissions)
            )
        except TypeError:
            self.ALLOW = self.BLOCK = self.REDIRECT = False
        self.compacted = ""
        if self.ALLOW:
            self.compacted += "A"
        if self.BLOCK:
            self.compacted += "B"
        if self.REDIRECT:
            self.compacted += "R"


class TBlockSyntaxStatus:
    """
    Names to use to tell the converter that the rule is in fact a TBlock status indication
    """

    CURRENT_STATUS = "TS"
    CURRENT_POLICY = "TP"


class RulePolicy:
    """
    Names to use to tell the converter which is the policy of the rule it is trying to convert
    """

    ALLOW = "A"
    BLOCK = "B"
    REDIRECT = "R"


class FilterSyntax:
    """
    List of supported syntax
    """

    ADBLOCKPLUS = "adblockplus"
    HOSTS = "hosts"
    DNSMASQ = "dnsmasq"
    LIST = "list"
    TBLOCK = "tblock"
    TBLOCK_LEGACY = "tblock_legacy"
    UNKNOWN = ""


class FilterSyntaxRegex:
    """
    Regex rules to detect which syntax is used
    """

    ADBLOCKPLUS = re.compile(r"^((@@)?\|\|[a-z\d\-.]+\^(\$(doc(ument)?|all))?|!.*)$")
    HOSTS = re.compile(r"^((\d{1,3}\.){3}\d{1,3}[\t ]+[a-z\d\-.*]+|#.*)$")
    DNSMASQ = re.compile(
        r"^(server=/[a-z\d\-.]+/|address=/[a-z\d\-.]+/(\d{1,3}\.){3}\d{1,3}/|#.*)$"
    )
    LIST = re.compile(r"^([a-z\d\-.*]+|#.*)$")
    TBLOCK_LEGACY = re.compile(
        r"^([a-z\d\-.]*\.[a-z]*|(@BEGIN_RULES|@END_RULES)|(!allow|!block|!redirect [\d.:a-f]*)|#.*)$"
    )
    TBLOCK = re.compile(
        r'^([a-z\d\-.]*\.[a-z]*|(\[allow]|\[block]|\[redirect "[\d.:a-f]*"])|#.*)$'
    )


class Profile:
    """
    This contains the different profiles that are available during the setup wizard
    """

    # pylint: disable=too-few-public-methods

    NONE = []
    LIGHT = NONE + ["peter-lowe", "stevenblack-hosts", "tblock-allow", "tblock-base"]
    BALANCED = LIGHT + ["adguard-cname", "adguard-dns", "cpbl-filters"]
    AGGRESSIVE = BALANCED + ["ddgtrackerradar", "divested", "mpvs-hosts"]


class Components:
    """
    This contains the different additional components that one can choose to block during the setup wizard
    """

    # pylint: disable=too-few-public-methods

    SECURITY = [
        "blocklistproject-phishing",
        "blocklistproject-ramsomware",
        "blocklistproject-malware",
        "spam404",
        "tblock-security",
        "urlhaus",
    ]
    PORNOGRAPHY = ["blocklistproject-porn"]
    FAKE_NEWS = ["fakenews"]
    DRUGS = ["blocklistproject-drugs"]
    GAMBLING = ["blocklistproject-gambling"]
    PIRACY = ["blocklistproject-piracy"]
    HATE = [
        "antifa-blocklist",
        "antifa-blocklist-alttech",
        "antifa-blocklist-populistic",
    ]
    CRYPTO = ["blocklistproject-crypto"]


# Code name to use to tell TBlock that a rule is a user-defined rule
USER_RULE_PRIORITY = "!user"

RULE_COMMENTS = "C"

USER_AGENT = """Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"""

WARNS = [
    "no issue detected",
    "may break some web pages",
    "may break some apps and web pages",
    "may slow boot or internet connection",
    "not recommended for daily use",
]

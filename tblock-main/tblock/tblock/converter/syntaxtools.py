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
import ipaddress

# Local modules
from ..exceptions import FilterSyntaxError
from ..const import (
    FilterSyntax,
    FilterSyntaxRegex,
    TBlockSyntaxStatus,
    RulePolicy,
    RULE_COMMENTS,
)


def detect_syntax(line_list: list) -> str:
    rules = []

    # Remove blank lines from test
    for rule in line_list:
        if rule != "\n":
            rules.append(rule.split("\n")[0])

    # Count the number of lines that are not empty
    rules_count = len(rules)

    # Convert that list into a string, in order to use regex to find patterns in it
    rules = str(rules)

    # Check the syntax of the filter using regex and calculating the percentage of rules that match a syntax
    if re.findall(re.compile(r"(\[adblock plus)", re.IGNORECASE), rules):
        return FilterSyntax.ADBLOCKPLUS
    elif re.findall(re.compile(r"@BEGIN_RULES|@END_RULES"), rules):
        return FilterSyntax.TBLOCK_LEGACY
    elif re.findall(re.compile(r'(\[allow]|\[block]|\[redirect "[\d.:a-f]"*])'), rules):
        return FilterSyntax.TBLOCK
    elif (
        len(re.findall(re.compile(r"(\|\|[.a-z\-]*[$^]|![ A-z]*[.]*:|!)"), rules))
        * 100
        / rules_count
        >= 50
    ):
        return FilterSyntax.ADBLOCKPLUS
    elif (
        len(re.findall(re.compile(r"(server=/|address=/)"), rules)) * 100 / rules_count
        >= 50
    ):
        return FilterSyntax.DNSMASQ
    elif (
        len(
            re.findall(
                re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[ \t]*|::1[ \t]*"), rules
            )
        )
        * 100
        / rules_count
        >= 50
    ):
        return FilterSyntax.HOSTS
    elif (
        len(re.findall(re.compile(r"([\da-z]*\.[.a-z]*)"), rules)) * 100 / rules_count
        >= 50
    ):
        return FilterSyntax.LIST
    else:
        return FilterSyntax.UNKNOWN


def is_valid_rule(rule: str, syntax: str) -> bool:
    if syntax == FilterSyntax.ADBLOCKPLUS:
        return bool(re.match(FilterSyntaxRegex.ADBLOCKPLUS, rule))
    elif syntax == FilterSyntax.HOSTS:
        return bool(re.match(FilterSyntaxRegex.HOSTS, rule))
    elif syntax == FilterSyntax.LIST:
        return bool(re.match(FilterSyntaxRegex.LIST, rule))
    elif syntax == FilterSyntax.DNSMASQ:
        return bool(re.match(FilterSyntaxRegex.DNSMASQ, rule))
    elif syntax == FilterSyntax.TBLOCK_LEGACY:
        return bool(re.match(FilterSyntaxRegex.TBLOCK_LEGACY, rule))
    elif syntax == FilterSyntax.TBLOCK:
        return bool(re.match(FilterSyntaxRegex.TBLOCK, rule))
    else:
        raise FilterSyntaxError(f"invalid syntax: {syntax}")


def get_rule(
    rule: str,
    syntax: str,
    allow_comments: bool = False,
    tblock_policy: str = None,
    tblock_begin: bool = False,
    tblock_ip=None,
    allow_allow: bool = True,
    allow_block: bool = True,
    allow_redirect: bool = True,
) -> list:
    rule = rule.split("\n")[0]

    if syntax == FilterSyntax.ADBLOCKPLUS:
        if rule[0:4] == "@@||" and allow_allow:
            policy = RulePolicy.ALLOW
            domain = rule.split("||")[1].split("^")[0]
            return [domain, policy]
        elif rule[0:2] == "||" and allow_block:
            policy = RulePolicy.BLOCK
            domain = rule.split("||")[1].split("^")[0]
            return [domain, policy]
        elif rule[0:1] == "!" and allow_comments:
            policy = RULE_COMMENTS
            domain = rule.split("!")[1]
            return [domain, policy]
        else:
            return []

    elif syntax == FilterSyntax.HOSTS:
        if (
            rule[0:4] == "127." or rule[0:2] == "0." or rule[:3] == "::1"
        ) and allow_block:
            policy = RulePolicy.BLOCK
            rule_split = rule.split(" ")
            rule_split_tab = rule_split[len(rule_split) - 1].split("\t")
            domain = rule_split_tab[len(rule_split_tab) - 1]
            return [domain, policy]
        elif rule[0:1] == "#" and allow_comments:
            domain = rule.split("#")[1]
            return [domain, RULE_COMMENTS]
        elif allow_redirect:
            rule_split = rule.split(" ")
            try:
                ip = ipaddress.ip_address(rule_split[0])
            except ValueError:
                # IP address is invalid
                return []
            else:
                rule_split_tab = rule_split[len(rule_split) - 1].split("\t")
                domain = rule_split_tab[len(rule_split_tab) - 1]
                return [domain, RulePolicy.REDIRECT, ip]

    elif syntax == FilterSyntax.DNSMASQ:
        if rule[0:8] == "server=/" and allow_block:
            policy = RulePolicy.BLOCK
            domain = rule.split("/")[1]
            return [domain, policy]
        elif rule[0:9] == "address=/":
            try:
                ip = ipaddress.ip_address(rule.split("/")[2])
            except IndexError:
                if allow_block:
                    return [rule.split("/")[1], RulePolicy.BLOCK]
            except ValueError:
                return []
            else:
                if ip.is_loopback or ip.compressed[0:2] == "0." and allow_block:
                    policy = RulePolicy.BLOCK
                    domain = rule.split("/")[1]
                    return [domain, policy]
                elif allow_redirect:
                    domain = rule.split("/")[1]
                    return [domain, RulePolicy.REDIRECT, ip]
        elif rule[0:1] == "#" and allow_comments:
            domain = rule.split("#")[1]
            return [domain, RULE_COMMENTS]

    elif syntax == FilterSyntax.TBLOCK:
        if rule[0] == "[" and rule[-1] == "]":
            ip = None
            policy_text = rule.split("[")[1].split("]")[0]
            if policy_text == "block":
                policy = RulePolicy.BLOCK
            elif policy_text == "allow":
                policy = RulePolicy.ALLOW
            elif policy_text[0:10] == 'redirect "' and policy_text[-1] == '"':
                policy = RulePolicy.REDIRECT
                ip = ipaddress.ip_address(policy_text.split('"')[1].split('"')[0])
            else:
                return []
            if policy == RulePolicy.REDIRECT:
                return [TBlockSyntaxStatus.CURRENT_POLICY, policy, ip]
            else:
                return [TBlockSyntaxStatus.CURRENT_POLICY, policy]
        elif not rule[0:1] == "#":
            if tblock_policy is not None:
                if tblock_policy == RulePolicy.REDIRECT and allow_redirect:
                    return [rule, tblock_policy, tblock_ip]
                elif tblock_policy == RulePolicy.ALLOW and allow_allow:
                    return [rule, tblock_policy]
                elif tblock_policy == RulePolicy.BLOCK and allow_block:
                    return [rule, tblock_policy]
        elif allow_comments:
            return [rule.split("#")[1], RULE_COMMENTS]

    elif syntax == FilterSyntax.TBLOCK_LEGACY:
        if tblock_begin and rule[0:1] == "!":
            try:
                ip = None
                policy_text = rule.split("!")[1]
                if policy_text == "block":
                    policy = RulePolicy.BLOCK
                elif policy_text == "allow":
                    policy = RulePolicy.ALLOW
                elif policy_text[0:8] == "redirect":
                    policy = RulePolicy.REDIRECT
                    ip = ipaddress.ip_address(policy_text.split("redirect ")[1])
                else:
                    return []
            except (IndexError, ValueError):
                return []
            else:
                if policy == RulePolicy.REDIRECT:
                    return [TBlockSyntaxStatus.CURRENT_POLICY, policy, ip]
                else:
                    return [TBlockSyntaxStatus.CURRENT_POLICY, policy]
        elif rule == "@BEGIN_RULES":
            tblock_begin = True
            return [TBlockSyntaxStatus.CURRENT_STATUS, tblock_begin]
        elif rule == "@END_RULES":
            tblock_begin = False
            return [TBlockSyntaxStatus.CURRENT_STATUS, tblock_begin]
        elif not rule[0:1] == "#":
            if tblock_begin and tblock_policy is not None:
                if tblock_policy == RulePolicy.REDIRECT and allow_redirect:
                    return [rule, tblock_policy, tblock_ip]
                elif tblock_policy == RulePolicy.ALLOW and allow_allow:
                    return [rule, tblock_policy]
                elif tblock_policy == RulePolicy.BLOCK and allow_block:
                    return [rule, tblock_policy]
        elif allow_comments:
            return [rule.split("#")[1], RULE_COMMENTS]

    elif syntax == FilterSyntax.LIST and allow_block:
        domain = rule.split("\n")[0]
        if not domain[0:1] == "#":
            return [domain, RulePolicy.BLOCK]
        elif allow_comments:
            return [domain.split("#")[1], RULE_COMMENTS]

    else:
        raise FilterSyntaxError("invalid syntax: {0}".format(syntax))

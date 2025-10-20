#compdef tblock

# copy this file to /usr/share/zsh/site-functions/_tblock

# this file is based on the one from pacman(8)
# which is originaly released under GPL-2.0
# License: https://gitlab.archlinux.org/pacman/pacman/-/blob/master/COPYING
# Source: https://gitlab.archlinux.org/pacman/pacman/-/blob/master/scripts/completion/zsh_completion.in

typeset -A opt_args
setopt extendedglob

# options for passing to _arguments: main tblock commands
_tblock_opts_commands=(
    {-1,--init}'[Setup TBlock for the first time]'
    {-G,--gen-hosts}'[Generate hosts file template]'
    {-s,--status}'[Show status information]'
    {-v,--version}'[Display version and license information]'
    {-B,--build}'[Build hosts file]'
    {-D,--disable}'[Disable TBlock]'
    {-E,--enable}'[Enable TBlock]'
    {-a,--allow}'[Allow domain(s)]'
    {-b,--block}'[Block domain(s)]'
    {-r,--redirect}'[Redirect domain(s)]'
    {-d,--delete-rule}'[Delete rule(s)]'
    {-Y,--sync}'[Update filter list repository]'
    {-S,--subscribe}'[Subscribe to a list]'
    {-C,--add-custom}'[Subscribe to a custom list]'
    {-N,--rename}'[Rename a custom list]'
    {-R,--remove}'[Unubscribe from a list]'
    {-U,--update}'[Update all lists]'
    {-I,--info}'[Show info about a list]'
    {-l,--list-rules}'[List rules]'
    {-L,--list}'[List filter lists]'
    {-Q,--search}'[Search filter lists]'
    {-W,--which}'[Query filter list that manages a domain]'
    '(-h --help)'{-h,--help}'[Display help]'
)

# options for passing to _arguments: options common to all commands
_tblock_opts_common=(
    {-n,--no-prompt}'[Do not prompt for anything]'
    {-q,--quiet}'[Be the least verbose possible]'
)

# options for passing to _arguments: options for all filter lists operations
_tblock_opts_filters=(
    {-f,--force}'[Force the operation]'
)

# options for passing to _arguments: options for --subscribe, --remove, --update
_tblock_opts_with_sync=(
    {-y,--with-sync}'[Also update filter list repository]'
)

# options for passing to _arguments: options for --subscribe, --remove
_tblock_opts_with_update=(
    {-u,--with-update}'[Also update all filter lists]'
)

# options for passing to _arguments: options for all filter lists operations
_tblock_opts_list_filters=(
    {\*-c,\*--custom}'[Show custom filter lists only]'
    {\*-w,\*--on-repo}'[Show filter lists available in the filter list repository only]'
    {\*-k,\*--subscribing}'[Show subscribed filter lists only]'
    {\*-z,\*--not-subscribing}'[Show unsubscribed filter lists only]'
)

# options for passing to _arguments: options for all filter lists operations
_tblock_opts_list_rules=(
    {\*-e,\*--user}'[Show user rules only]'
    {\*-t,\*--standard}'[Show filter lists rules only]'
    {\*-m,\*--from-filters}'[Show rules coming from a specific filter list only]'
)

# handles cases where no subcommand has yet been given
_tblock_action_none() {
    _arguments -s : \
        "$_tblock_opts_commands[@]"
}

_tblock_action_default(){
    _arguments -s : \
        "$_tblock_opts_common[@]"
}

# handles --allow and --block subcommands
_tblock_action_allow_block() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        '*:rules:_hosts'
}

# handles --redirect subcommand
_tblock_action_redirect() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        {-i,--ip}'[Redirection IP address]' \
        '*:rules:_hosts'
}

# handles --delete-rule subcommand
_tblock_action_delete_rule() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        '*:rules:_tblock_completions_user_rules'
}

# handles --sync subcommand
_tblock_action_sync() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        "$_tblock_opts_filters[@]" \
}

# handles --subscribe subcommand
_tblock_action_subscribe() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        "$_tblock_opts_filters[@]" \
        "$_tblock_opts_with_sync[@]" \
        "$_tblock_opts_with_update[@]" \
        '*:filters:_tblock_completions_unsubscribed_lists'
}

# handles --add-custom subcommand
_tblock_action_add_custom() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        "$_tblock_opts_filters[@]" \
        "$_tblock_opts_with_sync[@]" \
        "$_tblock_opts_with_update[@]" \
        '*:files:_files'
}

# handles --rename subcommand
_tblock_action_rename() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        "$_tblock_opts_filters[@]" \
        "$_tblock_opts_with_sync[@]" \
        "$_tblock_opts_with_update[@]" \
        '*:filters:_tblock_completions_custom_lists'
}

# handles --remove subcommand
_tblock_action_unsubscribe() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        "$_tblock_opts_filters[@]" \
        "$_tblock_opts_with_sync[@]" \
        "$_tblock_opts_with_update[@]" \
        '*:filters:_tblock_completions_subscribed_lists'
}

# handles --update subcommand
_tblock_action_update() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        "$_tblock_opts_filters[@]" \
        "$_tblock_opts_with_sync[@]"
}

# handles --info subcommand
_tblock_action_info() {
    _arguments -s : \
        '*:filters:_tblock_completions_all_lists '
}

# handles --list and --search subcommands
_tblock_action_list() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        "$_tblock_opts_list_filters[@]" \
}

# handles --list-rules subcommand
_tblock_action_list_rules() {
    _arguments -s : \
        "$_tblock_opts_common[@]" \
        "$_tblock_opts_list_rules[@]" \
}

# handles --list-rules --from-filters subcommand
_tblock_action_list_rules_from() {
    _arguments -s : \
        '*:filters:_tblock_completions_subscribed_lists '
}

# handles --allow and --block subcommands
_tblock_action_which() {
    _arguments -s : \
        '*:rules:_hosts'
}

# provides completions for custom lists
_tblock_completions_custom_lists() {
    local -a cmd filters
    filters=( $(tblock -Lcq) )
    compadd "$@" -a filters
}

# provides completions for lists that are subsribed
_tblock_completions_subscribed_lists() {
    local -a cmd filters
    filters=( $(tblock -Lkq) )
    compadd "$@" -a filters
}

# provides completions for lists that are subscribed
_tblock_completions_unsubscribed_lists() {
    local -a cmd filters
    filters=( $(tblock -Lzq) )
    compadd "$@" -a filters
}

# provides completions for all lists
_tblock_completions_all_lists() {
    local -a cmd filters
    filters=( $(tblock -Lq) )
    compadd "$@" -a filters
}

# provides completions for all user rules
_tblock_completions_user_rules() {
    local -a cmd rules
    rules=( $(tblock -lqe) )
    compadd "$@" -a rules
}

# main dispatcher
_tblock_zsh_comp() {
    local -a args cmds
    local tmp
    args=( ${${${(M)words:#-*}#-}:#-*} )
    for tmp in $words; do
        cmds+=("${${_tblock_opts_commands[(r)*$tmp\[*]%%\[*}#*\)}")
    done
    case $args in #$words[2] in
        h*)
            return 0
            ;;
        1*)
            return 0
            ;;
        G*)
            return 0
            ;;
        s*)
            _tblock_action_default
            ;;
        v*)
            return 0
            ;;
        B*)
            _tblock_action_default
            ;;
        D*)
            _tblock_action_default
            ;;
        E*)
            _tblock_action_default
            ;;
        a*)
            _tblock_action_allow_block
            ;;
        b*)
            _tblock_action_allow_block
            ;;
        r*)
            _tblock_action_redirect
            ;;
        d*)
            _tblock_action_delete_rule
            ;;
        Y*)
            _tblock_action_sync
            ;;
        S*)
            _tblock_action_subscribe
            ;;
        C*)
            _tblock_action_add_custom
            ;;
        N*)
            _tblock_action_rename
            ;;
        R*)
            _tblock_action_unsubscribe
            ;;
        U*)
            _tblock_action_update
            ;;
        I*)
            _tblock_action_info
            ;;
        l*m*)
            _tblock_action_list_rules_from
            ;;
        l*)
            _tblock_action_list_rules
            ;;
        L*)
            _tblock_action_list
            ;;
        Q*)
            _tblock_action_list
            ;;
        W*)
            _tblock_action_which
            ;;
        *)

            case ${(M)words:#--*} in
                *--help*)
                    return 0
                    ;;
                *--init*)
                    return 0
                    ;;
                *--gen-hosts*)
                    return 0
                    ;;
                *--status*)
                    _tblock_action_default
                    ;;
                *--version*)
                    return 0
                    ;;
                *--build*)
                    _tblock_action_default
                    ;;
                *--disable*)
                    _tblock_action_default
                    ;;
                *--enable*)
                    _tblock_action_default
                    ;;
                *--allow*)
                    _tblock_action_allow_block
                    ;;
                *--block*)
                    _tblock_action_allow_block
                    ;;
                *--redirect*)
                    _tblock_action_redirect
                    ;;
                *--delete-rule*)
                    _tblock_action_delete_rule
                    ;;
                *--sync*)
                    _tblock_action_sync
                    ;;
                *--subscribe*)
                    _tblock_action_subscribe
                    ;;
                *--add-custom*)
                    _tblock_action_add_custom
                    ;;
                *--rename*)
                    _tblock_action_rename
                    ;;
                *--remove*)
                    _tblock_action_unsubscribe
                    ;;
                *--update*)
                    _tblock_action_update
                    ;;
                *--info*)
                    _tblock_action_info
                    ;;
                *--list-rules*)
                    _tblock_action_list_rules
                    ;;
                *--list*)
                    _tblock_action_list
                    ;;
                *--search*)
                    _tblock_action_list
                    ;;
                *--which*)
                    _tblock_action_which
                    ;;
                *)
                    _tblock_action_none
                    ;;
            esac
            ;;
    esac
}

_tblock_zsh_comp "$@"
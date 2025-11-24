#compdef mcp-skills

_mcp_skills_completion() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[mcp-skills] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _MCP_SKILLS_COMPLETE=zsh_complete mcp-skills)}")

    for type key descr in ${response}; do
        if [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        elif [[ "$type" == "dir" ]]; then
            _path_files -/
        elif [[ "$type" == "file" ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
    # autoload from fpath, call function directly
    _mcp_skills_completion "$@"
else
    # eval/source/. command, register function for later
    compdef _mcp_skills_completion mcp-skills
fi


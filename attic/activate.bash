_base_path="$(dirname "${BASH_SOURCE[0]}")"
eval "$(
    "${_base_path}/.local/utilities/micromamba" \
        --root-prefix "${_base_path}/.local/installations/micromamba" \
        shell hook --shell=bash)"
"${_base_path}/.local/utilities/micromamba" \
    --root-prefix "${_base_path}/.local/installations/micromamba" \
    activate langchain

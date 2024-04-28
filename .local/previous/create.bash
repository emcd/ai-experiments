#/usr/bin/env bash

set -eu -o pipefail

base_path="$(dirname "${BASH_SOURCE[0]}")"
mkdir --parents "${base_path}/.local"/{environments,installations,utilities}
PATH="${PATH}:${base_path}/.local/utilities"
#declare -r micromamba_cmd="${base_path}/.local/utilities/micromamba"
#if [[ ! -x "${micromamba_cmd}" ]]; then
#    echo 1>&2 "Retrieving Micromamba..."
#    curl --location --show-error \
#        "https://micro.mamba.pm/api/micromamba/linux-64/latest" \
#        | tar \
#            --directory "${base_path}/.local/utilities" \
#            --bzip2 --extract --strip-components 1 --verbose bin/micromamba
#fi
#export MAMBA_ROOT_PREFIX="${base_path}/.local/installations/micromamba"
#mkdir --parents "${MAMBA_ROOT_PREFIX}"
#eval "$(${micromamba_cmd} shell hook -s posix)"
#micromamba create --file "${base_path}/.local/configuration/conda.yaml"
#micromamba activate langchain
declare -r venv_path="${base_path}/.local/environments/langchain"
if [[ ! -d "${venv_path}" ]]; then
    python3 -m venv "${venv_path}"
    source "${venv_path}/bin/activate"
    python3 -m pip install --upgrade pip
    python3 -m pip install --requirement "${base_path}/.local/configuration/requirements.pip"
fi

set -eu -o pipefail
declare -r venv_name='langchain-venv'
rm --force --recursive "${venv_name}"
python3 -m venv "${venv_name}"
source "${venv_name}/bin/activate"
python3 -m pip install --upgrade pip
python3 -m pip install langchain notebook openai tomli

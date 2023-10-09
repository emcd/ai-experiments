## Installation

1. Clone this repository.
1. Ensure that you have Python 3.8 or newer installed with the complete
   standard library.
1. Run:
   ```
   python3 create-venv.py
   ```
1. Activate the virtual environment. In Bash, this would be done by:
   ```
   . .local/environments/langchain/bin/activate
   ```

## Update

1. Run:
   ```
   git pull
   ```
1. Activate the virtual environment, if not already active.
1. Run:
   ```
   python3 -m pip install --upgrade pip
   python3 -m pip install --upgrade --requirement .local/configuration/requirements.pip
   ```
Contains an application to interact with various AI providers, plus some
utilities to scrape data from the web and ingest into vector databases.


# Installation

## Initial Installation

1. Ensure that you have installed [Git LFS](https://git-lfs.com/).
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

## Installation Updates

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

# Configuration

## OpenAI Provider

1. Create a file named `.env` in the root directory of the Chatter application.

1. Add your OpenAI API key to the `.env` file in the following format:
   ```
   OPENAI_API_KEY = your_api_key_here
   ```
   Replace `your_api_key_here` with your actual OpenAI API key.

1. If you have an OpenAI organization ID, you can also add it to the `.env`
   file:
   ```
   OPENAI_ORGANIZATION_ID = your_organization_id_here
   ```
   Replace `your_organization_id_here` with your actual OpenAI organization ID.

1. Save the `.env` file. The Chatter application will automatically load these
   environment variables when it starts.

# Use

1. Activate the virtual environment. In Bash, this can be done with:
   ```
   . .local/environments/langchain/bin/activate
   ```
1. Run `chatter.py` using the Python interpreter:
   ```
   python3 chatter.py
   ```

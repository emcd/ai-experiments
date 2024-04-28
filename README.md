Contains an application to interact with various AI providers, plus some
utilities to scrape data from the web and ingest into vector databases.

# Use

NOTE: Please read the installation and configuration instructions before use.

Currently, there is no installable package, but you can run the application
via Hatch:
```
hatch run python chatter.py
```

# Installation

## Initial Installation

Currently, there is no installable package. But, the application can be setup
to run from a virtual environment without too much hassle by following these
steps:

1. Ensure that you have installed [Git LFS](https://git-lfs.com/).
1. Clone this repository.
1. Ensure that you have installed
   [Pipx](https://github.com/pypa/pipx/blob/main/README.md#install-pipx).
   (If installing via `pip`, you will want to use your system Python rather
   than the current global Python provided by Asdf, Mise, Pyenv, etc....)
1. Ensure that you have installed
   [Hatch](https://github.com/pypa/hatch/blob/master/README.md) via Pipx:
   ```
   pipx install hatch
   ```

## Installation Updates

1. Run:
   ```
   git pull
   ```
1. Remove the `default` virtual environment:
   ```
   hatch env remove default
   ```

The `default` virtual environment will be automatically rebuilt next time the
application is run via Hatch.

# Configuration

## OpenAI Provider

1. Create a file named `.env` in the same directory as this README file.
1. Add your OpenAI API key to the `.env` file in the following format:
   ```
   OPENAI_API_KEY=<your OpenAI API key>
   ```
1. If you have an OpenAI organization ID, you can also add it to the `.env`
   file:
   ```
   OPENAI_ORGANIZATION_ID=<your organization ID>
   ```

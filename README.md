Contains an application to interact with various AI providers, plus some
utilities to scrape data from the web and ingest into vector databases.

# Use

NOTE: Please read the installation and configuration instructions before use.

Currently, there is no installable package, but you can run the application
via Hatch:
```
hatch run aiwb
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

If you intend to develop on this project, then additionally perform:
1. Install Git pre-commit and pre-push hooks:
   ```
   hatch --env develop run pre-commit install --config .auxiliary/configuration/pre-commit.yaml
   ```
   and validate the installation with:
   ```
   hatch --env develop run pre-commit run --config .auxiliary/configuration/pre-commit.yaml --all-files
   ```

## Installation Updates

1. Run:
   ```
   git pull
   ```
1. Remove possibly-stale virtual environments:
   ```
   hatch env prune
   ```

The `default` virtual environment will be automatically rebuilt next time the
application is run via Hatch. You may need to run something in the `develop`
virtual environment to rebuild it too, if you have installed Git hooks which
rely upon it.

# Configuration

## General

A file, named `general.toml`, located in the user configuration directory for
the application, on first run. The user configuration directory varies by
platform:
* MacOS:
* Windows:
* XDG (Linux distributions, etc...): `~/.config/aiwb`
This file includes configurations for your AI providers, switches to enable or
disable special functionality, and the locations where your environment,
prompts, and conversations are stored.

## Environment

Environment variables are loaded from one of the following files:
1. An `.env` file in your current working directory.
1. An `.env` file in the same directory as this README.
1. The location from the `environment-file` entry in the general configuration
   (see above). By default, this is a file, named `environment`, in the user
   configuration directory.
The files are considered in the above order and only the first that exists is a
source for environment variables. The remainder are ignored.

Warning: If you keep your home directory, or pieces of it, in version control,
and you have an environment file in the user configuration directory for the
application, then you probably want to add the file location to `.gitignore`,
or equivalent, to avoid exposing sensitive credentials.

## AI Providers

### OpenAI

1. Add your OpenAI API key to the environment file as follows:
   ```
   OPENAI_API_KEY=<your OpenAI API key>
   ```
1. If you have an OpenAI organization ID, you can add it to the environment
   file:
   ```
   OPENAI_ORG_ID=<your organization ID>
   ```
1. If you have an OpenAI project ID, you can add it to the environment file:
   ```
   OPENAI_PROJECT_ID=<your project ID>
   ```

#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

# Specify the Python version
PYTHON_VERSION=3.12

if [[ "$(uname)" == "Darwin" ]]; then
  # macOS: use Homebrew
  if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Install it from https://brew.sh and re-run."
    exit 1
  fi

  if ! brew list "python@$PYTHON_VERSION" &> /dev/null; then
    echo "python@$PYTHON_VERSION not found, installing via brew..."
    brew install "python@$PYTHON_VERSION"
  else
    echo "python@$PYTHON_VERSION is already installed."
  fi

  if ! command -v uv &> /dev/null; then
    brew install uv
  fi
else
  # Linux: use apt-get and Astral installer
  install_if_not_exists() {
    if ! dpkg-query -W "$1" &> /dev/null; then
      echo "$1 could not be found, installing..."
      sudo apt-get install -y "$1"
    else
      echo "$1 is already installed."
    fi
  }

  sudo apt-get update
  install_if_not_exists "python$PYTHON_VERSION"

  if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env"
  fi
fi

# Wipe out the old virtual environment
[ -d .venv ] && rm -rf .venv

# Install dependencies from the SHA-locked lockfile
uv sync --python "$PYTHON_VERSION" --frozen

echo "Setup completed successfully."

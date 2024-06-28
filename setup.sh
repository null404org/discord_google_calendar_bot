#!/bin/bash
# Exit immediately if a command exits with a non-zero status
set -e

# Specify the Python version
PYTHON_VERSION=3.12

# Function to install a package if it's not already installed
install_if_not_exists() {
  #if ! command -v $1 &> /dev/null; then
  if ! dpkg-query -W $1 &> /dev/null; then
    echo "$1 could not be found, installing..."
    sudo apt-get install -y $1
  else
    echo "$1 is already installed."
  fi
}

# Update package list
sudo apt-get update

# Install Python and necessary packages
install_if_not_exists python$PYTHON_VERSION
install_if_not_exists python${PYTHON_VERSION}-venv
install_if_not_exists python3-pip

#
[ -d .venv ] && rm -rf .venv

# Create a virtual environment using the specified Python version
python$PYTHON_VERSION -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required Python packages from requirements.txt
[ -f requirements-dev.txt ] && pip install -r requirements-dev.txt || pip install -r requirements.txt

# Deactivate the virtual environment
deactivate

echo "Setup completed successfully."

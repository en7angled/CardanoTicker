#!/bin/bash

# Enable error handling: stop script execution on any error
set -e

# Define error trap
trap 'echo "Error occurred at line $LINENO. Exiting..." >&2' ERR

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$(realpath "$0")")
REPO_DIR=$(realpath "$SCRIPT_DIR/..")

# Get the current username
CURRENT_USER=$(whoami)

# Check if setup.py or pyproject.toml exists
if [ ! -f "$REPO_DIR/setup.py" ] && [ ! -f "$REPO_DIR/pyproject.toml" ]; then
  echo "Error: Could not find setup.py or pyproject.toml in $REPO_DIR"
  echo "Make sure you are running this script inside the cloned Cardano Ticker repository."
  exit 1
fi

# Prompt the user to choose virtual environment setup
echo "Do you want to use a virtual environment for installation? (recommended)"
echo "Type 'yes' to use venv or 'no' to install system-wide with sudo:"
read -r USE_VENV

# Virtual environment path
VENV_DIR="$REPO_DIR/venv"

if [[ "$USE_VENV" == "yes" ]]; then
  # Ensure python3-venv is installed
  if ! python3 -m venv --help &> /dev/null; then
    echo "Error: python3-venv is not installed. Install it with:"
    echo "  sudo apt-get install python3-venv -y"
    exit 1
  fi

  # Remove existing venv if it's corrupted
  if [ -d "$VENV_DIR" ]; then
    echo "Removing existing virtual environment..."
    rm -rf "$VENV_DIR"
  fi

  # Create virtual environment
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"

  # Verify venv was created successfully
  if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Error: Virtual environment creation failed!"
    exit 1
  fi
  echo "Virtual environment created successfully."

  # Activate the virtual environment
  echo "Activating virtual environment..."
  source "$VENV_DIR/bin/activate"

  # Upgrade pip inside the virtual environment
  echo "Upgrading pip..."
  pip install --upgrade pip

  # Install provider dependencies
  echo "Installing provider dependencies..."
  cd "$REPO_DIR"
  if pip install .; then
    echo "Provider dependencies installed successfully."
  else
    echo "Error: Failed to install provider dependencies." >&2
    exit 1
  fi

else
  # System-wide installation using sudo
  echo "Installing system-wide using sudo..."
  cd "$REPO_DIR"
  if sudo pip install .; then
    echo "Provider dependencies installed successfully."
  else
    echo "Error: Failed to install provider dependencies." >&2
    exit 1
  fi
fi

# Copy and edit config
CONFIG_PATH="/home/$CURRENT_USER/cardano_ticker_config.json"
if [ ! -f "$CONFIG_PATH" ]; then
  echo "Copying configuration file..."
  cp "$REPO_DIR/src/cardano_ticker/data/config.json" "$CONFIG_PATH"
  echo "Configuration file copied to $CONFIG_PATH. Please edit this file to add your Blockfrost API key."
else
  echo "Configuration file already exists at $CONFIG_PATH."
fi

# Set environment variable in .bashrc
if ! grep -q "TICKER_CONFIG_PATH" ~/.bashrc; then
  echo "Setting TICKER_CONFIG_PATH environment variable..."
  echo "export TICKER_CONFIG_PATH=$CONFIG_PATH" >> ~/.bashrc
  echo "Environment variable added to .bashrc."
fi
source ~/.bashrc

# Create provider systemd service
echo "Creating provider systemd service..."
sudo bash -c "cat <<EOF > /etc/systemd/system/cardano-ticker-provider.service
[Unit]
Description=Cardano Ticker Provider
After=network.target

[Service]
ExecStart=$([[ "$USE_VENV" == "yes" ]] && echo "$VENV_DIR/bin/python" || echo "/usr/bin/python3") "$REPO_DIR/src/cardano_ticker/dashboards/dashboard_provider.py"
WorkingDirectory=$REPO_DIR
Environment=\"TICKER_CONFIG_PATH=$CONFIG_PATH\"
Restart=always
User=$CURRENT_USER
Group=$(id -gn $CURRENT_USER)

[Install]
WantedBy=multi-user.target
EOF"
sudo systemctl daemon-reload
sudo systemctl enable cardano-ticker-provider
sudo systemctl start cardano-ticker-provider
echo "Provider service set up and started successfully."

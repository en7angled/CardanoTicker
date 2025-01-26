#!/bin/bash

# Enable error handling: stop script execution on any error
set -e

# Define error trap
trap 'echo "Error occurred at line $LINENO. Exiting..." >&2' ERR

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$(realpath "$0")")
REPO_DIR=$(realpath "$SCRIPT_DIR/..")
echo  $REPO_DIR
# Get the current username
CURRENT_USER=$(whoami)

# Prompt the user to choose virtual environment setup
echo "Do you want to use a virtual environment for installation? (recommended)"
echo "Type 'yes' to use venv or 'no' to install system-wide with --break-system-packages:"
read -r USE_VENV

# Virtual environment path
VENV_DIR="$REPO_DIR/venv"

if [[ "$USE_VENV" == "yes" ]]; then
  # Using virtual environment
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created successfully."
  fi

  # Check if the activate script exists and source it
  ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
  if [ -f "$ACTIVATE_SCRIPT" ]; then
    echo "Activating virtual environment..."
    source "$ACTIVATE_SCRIPT"
  else
    echo "Error: Activate script not found in $VENV_DIR/bin/activate" >&2
    exit 1
  fi

  # Upgrade pip inside the virtual environment
  echo "Upgrading pip..."
  pip install --upgrade pip

  cd $REPO_DIR
  # Install provider dependencies
  echo "Installing provider dependencies..."
  if pip install .; then
    echo "Provider dependencies installed successfully."
  else
    echo "Error: Failed to install provider dependencies." >&2
    exit 1
  fi

  # Install display dependencies
  echo "Installing display dependencies..."
  cd ./src/displayers/waveshare || exit
  if pip install -r requirements.txt; then
    echo "Display dependencies installed successfully."
  else
    echo "Error: Failed to install display dependencies." >&2
    exit 1
  fi
else
  cd $REPO_DIR
  # System-wide installation with --break-system-packages
  echo "Installing system-wide with --break-system-packages..."
  if pip install . --break-system-packages; then
    echo "Provider dependencies installed successfully."
  else
    echo "Error: Failed to install provider dependencies." >&2
    exit 1
  fi

  # Install display dependencies system-wide
  echo "Installing display dependencies system-wide..."
  cd ./src/displayers/waveshare || exit
  if pip install -r requirements.txt --break-system-packages; then
    echo "Display dependencies installed successfully."
  else
    echo "Error: Failed to install display dependencies." >&2
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
ExecStart=$([[ "$USE_VENV" == "yes" ]] && echo "$VENV_DIR/bin/python" || echo "/usr/bin/python3")  "$REPO_DIR/src/cardano_ticker/dashboards/dashboard_provider.py"
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

# Create displayer systemd service
echo "Creating displayer systemd service..."
sudo bash -c "cat <<EOF > /etc/systemd/system/cardano-ticker-displayer.service
[Unit]
Description=Cardano Ticker Displayer
After=network.target

[Service]
ExecStart=$([[ "$USE_VENV" == "yes" ]] && echo "$VENV_DIR/bin/python" || echo "/usr/bin/python3") $REPO_DIR/src/displayers/waveshare/display.py epd4in01f $REPO_DIR/src/cardano_ticker/data/frame.bmp
WorkingDirectory=$REPO_DIR/src/displayers/waveshare
Restart=always
User=$CURRENT_USER
Group=$(id -gn $CURRENT_USER)

[Install]
WantedBy=multi-user.target
EOF"
sudo systemctl daemon-reload
sudo systemctl enable cardano-ticker-displayer
sudo systemctl start cardano-ticker-displayer
echo "Displayer service set up and started successfully."

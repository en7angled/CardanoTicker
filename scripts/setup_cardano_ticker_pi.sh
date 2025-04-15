#!/bin/bash

# Enable error handling: stop script execution on any error
set -e

# Define error trap
trap 'echo "Error occurred at line $LINENO. Exiting..." >&2' ERR

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$(realpath "$0")")
REPO_DIR=$(realpath "$SCRIPT_DIR/..")
echo  "Repository Directory: $REPO_DIR"

# Get the current username
CURRENT_USER=$(whoami)

# Prompt the user for display type
echo "Which display type do you want to set up?"
echo "Type 'lcd' for an LCD display or 'epaper' for an e-paper display."
read -r DISPLAY_TYPE

# Ensure valid selection
if [[ "$DISPLAY_TYPE" != "lcd" && "$DISPLAY_TYPE" != "epaper" ]]; then
  echo "Invalid choice. Please restart and enter 'lcd' or 'epaper'."
  exit 1
fi

# If LCD is selected, ask for resolution
if [[ "$DISPLAY_TYPE" == "lcd" ]]; then
  echo "Enter the LCD resolution width (e.g., 800):"
  read -r LCD_WIDTH
  echo "Enter the LCD resolution height (e.g., 480):"
  read -r LCD_HEIGHT

  # Ensure width and height are numbers
  if ! [[ "$LCD_WIDTH" =~ ^[0-9]+$ ]] || ! [[ "$LCD_HEIGHT" =~ ^[0-9]+$ ]]; then
    echo "Error: Resolution width and height must be numeric values."
    exit 1
  fi
fi

# If e-paper is selected, ask for resolution and display type
if [[ "$DISPLAY_TYPE" == "epaper" ]]; then
  echo "Enter the e-paper resolution width (e.g., 640):"
  read -r EPAPER_WIDTH
  echo "Enter the e-paper resolution height (e.g., 400):"
  read -r EPAPER_HEIGHT
  echo "Enter the e-paper display type (default: epd4in01f):"
  read -r EPAPER_TYPE

  # Use default display type if empty
  if [[ -z "$EPAPER_TYPE" ]]; then
    EPAPER_TYPE="epd4in01f"
  fi

  # Ensure width and height are numbers
  if ! [[ "$EPAPER_WIDTH" =~ ^[0-9]+$ ]] || ! [[ "$EPAPER_HEIGHT" =~ ^[0-9]+$ ]]; then
    echo "Error: Resolution width and height must be numeric values."
    exit 1
  fi
fi

# Prompt the user to choose virtual environment setup
echo "Do you want to use a virtual environment for installation?"
echo "Type 'yes' to use venv or 'no' to install system-wide with --break-system-packages:  (recommended for Raspberry Pi Zero)"
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
  pip install . || { echo "Error: Failed to install provider dependencies." >&2; exit 1; }

  # Install display dependencies
  echo "Installing display dependencies..."
  if [[ "$DISPLAY_TYPE" == "epaper" ]]; then
    cd ./src/displayers/waveshare || exit
  else
    cd ./src/displayers/lcd || exit
  fi
  pip install -r requirements.txt || { echo "Error: Failed to install display dependencies." >&2; exit 1; }

else
  cd $REPO_DIR
  # System-wide installation
  echo "Installing system-wide with --break-system-packages..."
  pip install . --break-system-packages || { echo "Error: Failed to install provider dependencies." >&2; exit 1; }

  # Install display dependencies system-wide
  echo "Installing display dependencies system-wide..."
  if [[ "$DISPLAY_TYPE" == "epaper" ]]; then
    cd ./src/displayers/waveshare || exit
  else
    cd ./src/displayers/lcd || exit
  fi
  pip install -r requirements.txt --break-system-packages || { echo "Error: Failed to install display dependencies." >&2; exit 1; }
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

# modify config file output_dir field !
FRAME_OUTPUTDIR=$REPO_DIR/src/cardano_ticker/data/
if [ -f "$CONFIG_PATH" ]; then
  echo "Modifying configuration file..."
  sed -i "s|\"output_dir\":.*|\"output_dir\": \"$FRAME_OUTPUTDIR\",|" "$CONFIG_PATH"
  echo "Configuration file modified successfully."
else
  echo "Error: Configuration file not found at $CONFIG_PATH." >&2
  exit 1
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
After=network-online.target
Wants=network-online.target

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

# Create display systemd service based on selection
if [[ "$DISPLAY_TYPE" == "epaper" ]]; then
  DISPLAY_SCRIPT="src/displayers/waveshare/display.py $EPAPER_TYPE $REPO_DIR/src/cardano_ticker/data/frame.bmp $EPAPER_WIDTH $EPAPER_HEIGHT"
else
  DISPLAY_SCRIPT="src/displayers/lcd/display.py $REPO_DIR/src/cardano_ticker/data/frame.bmp $LCD_WIDTH $LCD_HEIGHT"
fi

echo "Creating displayer systemd service..."
sudo bash -c "cat <<EOF > /etc/systemd/system/cardano-ticker-displayer.service
[Unit]
Description=Cardano Ticker Displayer
After=network.target

[Service]
ExecStart=$([[ "$USE_VENV" == "yes" ]] && echo "$VENV_DIR/bin/python" || echo "/usr/bin/python3") $REPO_DIR/$DISPLAY_SCRIPT
WorkingDirectory=$REPO_DIR
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

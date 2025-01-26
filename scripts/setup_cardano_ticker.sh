#!/bin/bash

# Get the directory of the current script
SCRIPT_DIR=$(dirname "$(realpath "$0")")
REPO_DIR=$(realpath "$SCRIPT_DIR/..")

# Get the current username
CURRENT_USER=$(whoami)

# Virtual environment path
VENV_DIR="$REPO_DIR/venv"

# Check if virtual environment exists, create it if not
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# Check if the activate script exists and source it
ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
if [ -f "$ACTIVATE_SCRIPT" ]; then
  echo "Activating virtual environment..."
  source "$ACTIVATE_SCRIPT"
else
  echo "Error: Activate script not found in $VENV_DIR/bin/activate"
  exit 1
fi

# Upgrade pip inside the virtual environment
pip install --upgrade pip

# Install provider dependencies
cd $REPO_DIR
pip install .

# Copy and edit config
CONFIG_PATH="/home/$CURRENT_USER/cardano_ticker_config.json"
cp ./src/cardano_ticker/data/config.json "$CONFIG_PATH"
echo "Please edit $CONFIG_PATH to add your Blockfrost API key."

# Set environment variable in .bashrc
if ! grep -q "TICKER_CONFIG_PATH" ~/.bashrc; then
  echo "export TICKER_CONFIG_PATH=$CONFIG_PATH" >> ~/.bashrc
fi
source ~/.bashrc

# Create provider systemd service
sudo bash -c "cat <<EOF > /etc/systemd/system/cardano-ticker-provider.service
[Unit]
Description=Cardano Ticker Provider
After=network.target

[Service]
ExecStart=$VENV_DIR/bin/python -m cardano_ticker.provider
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
echo "Provider service set up and started."

# Navigate to the waveshare directory
cd ./src/displayers/waveshare || exit

# Install display dependencies
pip install -r requirements.txt

# Create displayer systemd service
sudo bash -c "cat <<EOF > /etc/systemd/system/cardano-ticker-displayer.service
[Unit]
Description=Cardano Ticker Displayer
After=network.target

[Service]
ExecStart=$VENV_DIR/bin/python $REPO_DIR/src/displayers/waveshare/display.py epd4in01f $REPO_DIR/src/cardano_ticker/data/frame.bmp
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
echo "Displayer service set up and started."

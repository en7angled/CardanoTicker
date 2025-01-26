#!/bin/bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip gpiod libgpiod-dev
sudo raspi-config nonint do_spi 0  # Enable SPI via raspi-config
echo "Raspberry Pi setup complete."

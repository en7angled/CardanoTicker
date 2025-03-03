
# **Getting Started: Cardano Ticker Installation Guide**

This guide walks you through setting up the Cardano Ticker for the connected version using a Raspberry Pi Zero 2W. The process has been streamlined with setup scripts for easy installation.

---

## **1. Prerequisites**

Before starting, ensure you have the following items:
- Raspberry Pi (3 / 4/ 5 / Zero 2W)
- MicroSD card (16GB or larger, Class 10 or better)
- Power adapter
- Internet connection (Wi-Fi or Ethernet via an adapter)
- Cardano Ticker hardware components (e-paper/lcd display, buttons, etc.)

---

## **2. Raspberry Pi Setup**

1. **Download and Install Raspberry Pi OS:**
   - Download the latest Raspberry Pi OS Lite (recommended for minimal resource usage) from the official Raspberry Pi website.
   - Use Raspberry Pi Imager or balenaEtcher to write the OS image to your MicroSD card.

2. **Boot and Configure the Pi:**
   - Insert the MicroSD card into the Pi and power it on.
   - Follow the setup wizard to configure Wi-Fi, locale, and SSH (optional).

3. **Download the Repository and Setup Scripts:**
   - Clone the entire Cardano Ticker repository to your Pi:
     ```bash
     git clone https://github.com/en7angled/CardanoTicker.git
     cd CardanoTicker
     ```

4. **Run the `setup_pi.sh` Script:**
   - Navigate to the `scripts` directory and execute the `setup_pi.sh` script:
     ```bash
     cd scripts
     chmod +x setup_pi.sh
     ./setup_pi.sh
     ```
   - The script performs the following:
     - Updates system packages.
     - Installs Python, `pip`, and GPIO libraries.
     - Enables the SPI interface.

   After running the script, your Raspberry Pi will be ready for the Cardano Ticker setup.

---

## **3. Cardano Ticker Installation**

1. **Run the `setup_cardano_ticker_pi.sh` Script:**
   - From the `scripts` directory, execute the `setup_cardano_ticker_pi.sh` script:
     ```bash
     chmod +x setup_cardano_ticker_pi.sh
     ./setup_cardano_ticker_pi.sh
     ```

   **Script Features:**
   - **Option to Use Virtual Environment:**
     The script prompts you to choose whether to install dependencies in a `venv` (recommended) or system-wide with `--break-system-packages`.
   - **Provider Setup:**
     - Installs Python dependencies.
     - Copies and configures the `config.json` file.
     - Sets up the `cardano-ticker-provider` systemd service.
   - **Displayer Setup:**
     - Installs dependencies for the Waveshare e-paper display.
     - Sets up the `cardano-ticker-displayer` systemd service.

---

## **4. Configuration**

- **Edit the Configuration File:**
  After running the setup script, update the `config.json` file with your Blockfrost API key:
  ```bash
  nano /home/pi/cardano_ticker_config.json
  ```
  Replace `YOUR_PROJECT_ID` with the API key from [Blockfrost.io](https://blockfrost.io/).

- **Restart Services After Configuration:**
  ```bash
  sudo systemctl restart cardano-ticker-provider
  sudo systemctl restart cardano-ticker-displayer
  ```

---

## **5. Troubleshooting**

- **Service Logs:**
  Check the logs if the services do not start:
  ```bash
  journalctl -u cardano-ticker-provider -f
  journalctl -u cardano-ticker-displayer -f
  ```

- **Verify SPI Interface:**
  Ensure the SPI interface is enabled:
  ```bash
  lsmod | grep spi
  ```

- **Check Internet Connection:**
  Verify that the Pi is connected to the internet to fetch data and install dependencies.

---

## **6. Next Steps**

Once both services are running:
- Assemble the Cardano Ticker hardware using the provided components and 3D-printed case design.
- Verify the display shows real-time Cardano blockchain data.

For updates, additional features, or troubleshooting, visit the [GitHub repository](https://github.com/en7angled/CardanoTicker).

---

# CardanoTicker Installation Guide for ESP32

## Overview
This guide explains how to install and configure the **CardanoTicker** for the ESP32 version. The system consists of two main components:
1. **Server (Dashboard Provider)** - Runs on a PC to fetch and process blockchain data.
2. **Displayer** - Runs on the ESP32 to render and display the processed data.

## Prerequisites
### Hardware Requirements
- ESP32 microcontroller
- Waveshare e-paper display (or other compatible displays)
- Power supply for ESP32

### Software Requirements
- A PC with Linux/macOS/Windows (for the server)
- ESP32 support installed in **Arduino IDE**
- Required ESP32 libraries (listed below)
- WiFi credentials and server details

## 1. Setting Up the Server (Dashboard Provider)
The server is responsible for fetching blockchain data and generating dashboard images.

### Steps:
1. Clone the repository:
   ```sh
   git clone https://github.com/en7angled/CardanoTicker.git
   cd CardanoTicker
   ```
2. Run the setup script on your PC:
   ```sh
   ./scripts/setup_cardano_ticker_linux.sh
   ```
   This installs dependencies and sets up the server environment.
3. Edit the Configuration File:
  After running the setup script, update the `config.json` file with your Blockfrost API key:
  ```bash
  nano /home/[username]/cardano_ticker_config.json
  ```
  Replace `YOUR_PROJECT_ID` with the API key from [Blockfrost.io](https://blockfrost.io/).
  You can also edit some other settings from the config as you see fit.

- Restart Services After Configuration:**
  ```bash
  sudo systemctl restart cardano-ticker-provider
  Ensure that the server is running and accessible over the network. 
  The server exposes two different types of the dashboard (color and bw):
  http://127.0.0.1:5335/latest-image
  http://127.0.0.1:5335/latest-image-bw

## 2. Setting Up the Displayer (ESP32)
### Steps:
1. Install **Arduino IDE** and add ESP32 board support.
2. Clone the ESP32 displayer code:
   ```sh
   cd CardanoTicker/src/displayers/esp32
   ```
3. Update the **displayer configuration**:
   - Open `displayer/displayer_config.h`
   - Modify the following fields with your network and server details:
     ```cpp
     #define WIFI_SSID "Your_WiFi_SSID"
     #define WIFI_PASSWORD "Your_WiFi_Password"
     #define SERVER_URL "http://your-server-ip:port"
     ```
4. Open **Arduino IDE** and load the project.
5. Install the required libraries:
   - **GFX Library** for rendering
   - **WiFiClient** for network connectivity
6. Compile and upload the code to ESP32.

## 3. Display Compatibility
The ESP32 displayer currently supports Waveshare e-paper displays. If using a different display, implement the `display_handler` interface:
- Path: `src/displayers/esp32/libraries/waveshare`
- Reference implementation: [Waveshare Libraries](https://github.com/en7angled/CardanoTicker/tree/main/src/displayers/esp32/libraries/waveshare)

For more details on Waveshare displays and ESP32 driver boards, refer to:
- [Waveshare ESP32 Driver Board Documentation](https://www.waveshare.com/wiki/E-Paper_ESP32_Driver_Board)

## 4. Pin Mapping for Waveshare E-Paper Displays
| PIN  | ESP32  | Description |
|------|--------|-------------|
| VCC  | 3V3    | Power (3.3V) |
| GND  | GND    | Ground |
| DIN  | P14    | SPI MOSI (Data Input) |
| SCLK | P13    | SPI CLK (Clock Input) |
| CS   | P15    | Chip Select (Active Low) |
| DC   | P27    | Data/Command Select |
| RST  | P26    | Reset (Active Low) |
| BUSY | P25    | Busy Status Output |

## Final Steps
- Ensure both the server and ESP32 displayer are running.
- The ESP32 should successfully fetch and render the dashboard.
- Debugging can be done using the Serial Monitor in **Arduino IDE**.

### Troubleshooting
- **ESP32 not connecting to WiFi?** Check `displayer_config.h` for correct credentials.
- **Dashboard not loading?** Ensure the server is running and accessible.
- **Custom display not supported?** Implement the `display_handler` interface from the [waveshare library](https://github.com/en7angled/CardanoTicker/tree/main/src/displayers/esp32/libraries/waveshare).

---
For further details, visit the [CardanoTicker GitHub Repository](https://github.com/en7angled/CardanoTicker).

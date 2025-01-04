
# Functional Specifications for Cardano Ticker Project

---

## 1. Overview
The Cardano Ticker project provides a compact, DIY cryptocurrency tracking device displaying real-time data on the Cardano blockchain. It combines low-cost hardware with an easy-to-assemble 3D-printed case and intuitive software dashboards for monitoring critical metrics.

---

## 2. Key Features
1. **Dynamic Data Display:**
   - Real-time price updates for ADA (Cardano).
   - Network statistics, including staking metrics and node status.
   - Blockchain synchronization progress.

2. **Multiple Display Options:**
   - Static e-paper display for low-power builds.
   - Dynamic LCD display for higher refresh rates.

3. **Wireless Connectivity:**
   - Wi-Fi-enabled updates for data fetching.
   - Optional battery-powered operation for portable setups.

4. **Open-Source and Expandable:**
   - Hosted on GitHub with community contributions encouraged.
   - Flexible software framework allowing feature expansions.

---

## 3. Hardware Requirements
1. **Raspberry Pi Zero 2W or ESP32 (alternative low-power version)**
2. **Display Modules:**
   - E-paper (Waveshare 4.01-inch) or LCD display.
3. **Power Options:**
   - USB charger for non-portable versions.
   - Battery pack for portable versions.
4. **3D-printed Case:**
   - Snap-fit or sliding mechanism for easy assembly.
   - Compatible with common 3D printer formats (STL, OBJ).
5. **MicroSD card**
   - only required for non-portable standalone version
8. **Buttons and Sensors (Optional):**
   - For user interactions or future extensions.
     
---

## 4. Software Functionalities
### 4.1 Data Fetching Module
- Periodically fetches data from Cardano blockchain APIs.
- Includes caching to handle network interruptions.

### 4.2 Display Management Module
- Dynamically updates screens based on the selected display type.
- Allows switching between dashboards (price, node, blockchain).

### 4.3 Configuration Module
- Provides initial setup through a web interface or USB configuration file.
- Allows customization of update intervals and data sources.

### 4.4 Dashboard Mock-ups
#### 1. Price Information Dashboard:
- Displays current ADA price in multiple currencies.
- Includes percentage change and price trends.

#### 2. Blockchain Dashboard:
- Shows network status, slot height, and block progress.
- Displays epoch and slot details.

#### 3. Node Dashboard:
- Provides node synchronization status.
- Displays peer connections and uptime.

---

## 5. Data Sources
- **API Integrations:**
  - BlockFrostApi or CryptoCompare for price updates.
  - BlockFrostApi, Cardano Explorer APIs for network statistics.
  - Easy to integrate other API providers and data sources
- **Fallback Mechanisms:**
  - Local cache for offline scenarios.
---

## 6. Compatibility
- **Operating System Support:**
  - Raspberry Pi OS (Lite or Full).
  - ESP-IDF (for ESP32 builds).
- **File Formats:**
  - STL, OBJ, 3MF for 3D printing.
- **Connectivity:**
  - Wi-Fi or USB for updates.

---

## 7. Testing and Validation
- **Hardware Tests:**
  - Fit and alignment of 3D-printed components.
  - Functionality tests for all hardware modules.
- **Software Tests:**
  - API response validation.
  - Display refresh tests.
---

## 8. User Feedback Mechanisms
1. GitHub Issues for reporting bugs.
2. Pull requests for community contributions.

---

## 9. Deployment and Delivery
- **GitHub Repository:**
  - Hosting code, documentation, and 3D files.
- **Thingiverse/Printables:**
  - STL files for 3D printing.
- **Documentation:**
  - Step-by-step assembly and configuration guides.

---

## 10. Future Roadmap
1. Integration with additional blockchains.
2. Enhanced data visualization tools.
3. Battery optimization for longer runtimes.


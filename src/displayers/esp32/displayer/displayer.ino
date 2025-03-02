#include <WiFi.h>
#include <HTTPClient.h>
#include <display_handler.h> // Generic display interface
#include <displayer_config.h>
#include <image_fetch_decode.h>


 // !!!! Specific display implementation, Replace with your own
#include <epd_4in01f_col.h>


void connectWiFi() {
    Serial.print("Connecting to WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println(" Connected!");
}


void setup() {
    Serial.begin(115200);
    connectWiFi();

    //print available heap memory
    Serial.println("Initializing display...");
    DisplayHandler* display = new EPD_4IN01F_Displayer(); // Assign specific display instance();

    Serial.println("Display initialising!");
    display->init();

    Serial.println("Clear!");
    display->clear();
    fetchAndDecodeBMP(display, display->getWidth(), display->getHeight());
    display->update();

    Serial.println("Going to deep sleep...");
    esp_sleep_enable_timer_wakeup(600 * 1000000);
    esp_deep_sleep_start();
}

void loop() {}

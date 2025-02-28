#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include  <display_handler.h> // Generic display interface
#include  <epd_3in52.h>    // Specific display implementation, Replace with your own

String ssid, password, serverURL;

DisplayHandler* display; // Pointer to generic display interface

void loadConfig() {
    if (!SPIFFS.begin(true)) {
        Serial.println("Failed to mount SPIFFS");
        return;
    }
    File file = SPIFFS.open("/config.json", "r");
    if (!file) {
        Serial.println("Failed to open config file");
        return;
    }
    StaticJsonDocument<256> doc;
    DeserializationError error = deserializeJson(doc, file);
    if (error) {
        Serial.println("Failed to read config");
        return;
    }
    ssid = doc["ssid"].as<String>();
    password = doc["password"].as<String>();
    serverURL = doc["serverURL"].as<String>();
    file.close();
}

void connectWiFi() {
    Serial.print("Connecting to WiFi...");
    WiFi.begin(ssid.c_str(), password.c_str());
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    Serial.println(" Connected!");
}

void fetchAndDecodeBMP(uint8_t* imageBuffer, int width, int height) {
    HTTPClient http;
    http.begin(serverURL);
    int httpCode = http.GET();

    if (httpCode == HTTP_CODE_OK) {
        WiFiClient *stream = http.getStreamPtr();
        uint8_t bmpHeader[14];
        stream->readBytes(bmpHeader, 14);
        int dataOffset = bmpHeader[10] | (bmpHeader[11] << 8) | (bmpHeader[12] << 16) | (bmpHeader[13] << 24);
        uint8_t bmpHeaderFull[dataOffset - 14];
        stream->readBytes(bmpHeaderFull, dataOffset - 14);

        int bmpWidth = bmpHeaderFull[4] | (bmpHeaderFull[5] << 8);
        int bmpHeight = bmpHeaderFull[8] | (bmpHeaderFull[9] << 8);
        int bitDepth = bmpHeaderFull[14] | (bmpHeaderFull[15] << 8);

        if (bitDepth != 1) {
            Serial.println("Error: Only 1-bit BMPs are supported!");
            return;
        }

        bool isLandscape = bmpWidth > bmpHeight;
        int targetWidth = isLandscape ? height : width;
        int targetHeight = isLandscape ? width : height;
        Serial.println("===== BMP HEADER INFO =====");

        Serial.print("Width: "); Serial.println(bmpWidth);
        Serial.print("Height: "); Serial.println(bmpHeight);
        Serial.print("Bit Depth: "); Serial.println(bitDepth);
        Serial.print("Is Landscape: "); Serial.println(isLandscape ? "Yes" : "No");

        // Check available heap memory
        uint32_t freeMemory = ESP.getFreeHeap();
        int rowSize = ((bmpWidth + 31) / 32) * 4;
        int requiredMemory = rowSize * bmpHeight;

        Serial.print("Required Memory: "); Serial.print(requiredMemory / 1024.0); Serial.println(" KB");
        Serial.print("Free Memory: "); Serial.print(freeMemory / 1024.0); Serial.println(" KB");

        if (requiredMemory > freeMemory) {
            Serial.println("ERROR: Image too large for available memory.");
            return;
        }

        // Allocate buffer for BMP pixel data
        uint8_t *bmpData = (uint8_t*) malloc(requiredMemory);
        if (bmpData == NULL) {
            Serial.println("Error: Not enough memory to allocate BMP buffer!");
            return;
        }

        // Read BMP pixel data
        stream->readBytes(bmpData, requiredMemory);

        // **Compute downsampling scale**
        float scaleX = (float)bmpWidth / targetWidth;
        float scaleY = (float)bmpHeight / targetHeight;
        float scale = max(scaleX, scaleY);

        // Clear e-Paper buffer
        memset(imageBuffer, 0xFF, sizeof(imageBuffer));

        // **Extract and Rotate in One Pass**
        for (int y = 0; y < targetHeight; y++) {
            int bmpY = min((int)(y * scale), bmpHeight - 1);
            int bmpRowOffset = (bmpHeight - 1 - bmpY) * rowSize;

            for (int x = 0; x < targetWidth; x++) {
                int bmpX = min((int)(x * scale), bmpWidth - 1);
                int byteIndex = bmpX / 8;
                int bitIndex = 7 - (bmpX % 8);
                uint8_t bufferByte = bmpData[bmpRowOffset + byteIndex];

                int newX, newY;
                if (isLandscape) {
                    // **Rotated Mapping**
                    newX = y;
                    newY = targetWidth - x - 1;
                } else {
                    // **Direct Mapping**
                    newX = x;
                    newY = y;
                }

                int bufferByteIndex = (newY * (width / 8)) + (newX / 8);
                int bufferBitIndex = 7 - (newX % 8);

                bool isBlack = !(bmpData[(bmpHeight - 1 - bmpY) * rowSize + byteIndex] & (1 << bitIndex));
                display->setPixel(imageBuffer, newX, newY, isBlack ? 0 : 1);
            }
        }
        free(bmpData);
    } else {
        Serial.print("Failed to fetch image, error: ");
        Serial.println(httpCode);
    }
    http.end();
}

void setup() {
    Serial.begin(115200);
    loadConfig();
    connectWiFi();

    display = new EPD_3IN52(); // Assign specific display instance
    display->init();

    uint8_t* imageBuffer = display->getBuffer();
    fetchAndDecodeBMP(imageBuffer, display->getWidth(), display->getHeight());
    display->update();

    Serial.println("Going to deep sleep...");
    esp_sleep_enable_timer_wakeup(600 * 1000000);
    esp_deep_sleep_start();
}

void loop() {}

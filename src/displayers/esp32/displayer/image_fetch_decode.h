#ifndef IMAGE_FETCH_DECODE_H
#define IMAGE_FETCH_DECODE_H

#include <WiFi.h>
#include <HTTPClient.h>
#include <display_handler.h>
#include <displayer_config.h>


void readBMPHeader(WiFiClient *stream, int &bmpWidth, int &bmpHeight, int &bitDepth, int &dataOffset) {
    uint8_t bmpHeader[14];
    stream->readBytes(bmpHeader, 14);
    dataOffset = bmpHeader[10] | (bmpHeader[11] << 8) | (bmpHeader[12] << 16) | (bmpHeader[13] << 24);
    uint8_t bmpHeaderFull[dataOffset - 14];
    stream->readBytes(bmpHeaderFull, dataOffset - 14);

    bmpWidth = bmpHeaderFull[4] | (bmpHeaderFull[5] << 8);
    bmpHeight = bmpHeaderFull[8] | (bmpHeaderFull[9] << 8);
    bitDepth = bmpHeaderFull[14] | (bmpHeaderFull[15] << 8);
}

uint32_t extractColor(uint8_t *rowBuffer, int rowX, int bitDepth) {
    uint32_t color = 0;
    if (bitDepth == 1) {
        int byteIndex = rowX / 8;
        int bitIndex = 7 - (rowX % 8);
        color = !(rowBuffer[byteIndex] & (1 << bitIndex)) ? 0 : 1;
    } else if (bitDepth == 4) {
        int byteIndex = rowX / 2;
        if (rowX % 2 == 0)
            color = (rowBuffer[byteIndex] >> 4) & 0x0F;
        else
            color = rowBuffer[byteIndex] & 0x0F;
    } else if (bitDepth == 8) {
        color = rowBuffer[rowX];

    } else if (bitDepth == 24 || bitDepth == 32) {
        int pixelIndex = rowX * (bitDepth / 8);
        uint8_t bgra[4] = {rowBuffer[pixelIndex], rowBuffer[pixelIndex+1], rowBuffer[pixelIndex+2], rowBuffer[pixelIndex+3]};
        color = *(uint32_t*)bgra;
    }
    return color;
}

void logInfo(int bmpWidth, int bmpHeight, int bitDepth, bool rotate90, int targetWidth, int targetHeight) {
        Serial.println("===== BMP HEADER INFO =====");
        Serial.print("Width: "); Serial.println(bmpWidth);
        Serial.print("Height: "); Serial.println(bmpHeight);
        Serial.print("Bit Depth: "); Serial.println(bitDepth);
        Serial.print("rotate90: "); Serial.println(rotate90 ? "Yes" : "No");
        Serial.print("Target Width: "); Serial.println(targetWidth);
        Serial.print("Target Height: "); Serial.println(targetHeight);
}

void fetchAndDecodeBMP(DisplayHandler* display, int width, int height) {
    HTTPClient http;
    http.begin(SERVER_URL);
    int httpCode = http.GET();

    if (httpCode == HTTP_CODE_OK) {
        WiFiClient *stream = http.getStreamPtr();
        // Read BMP header
       int bmpWidth, bmpHeight, bitDepth, dataOffset;
        readBMPHeader(stream, bmpWidth, bmpHeight, bitDepth, dataOffset);

        bool rotate90 = (bmpWidth > bmpHeight) && (width < height);

        if (rotate90 && !display->supportsRotation()) {
            Serial.println("Error: Display does not support rotation!");
            return;
        }

        if (display->getSupportedBitDepth() < bitDepth) {
            Serial.println("Error: Display does not support the color depth of the image!");
            return;
        }

        // Calculate target width and height
        int targetWidth = rotate90 ? height : width;
        int targetHeight = rotate90 ? width : height;


        logInfo(bmpWidth, bmpHeight, bitDepth, rotate90, targetWidth, targetHeight);

        // Check if the image is too small for the display
        if (bmpWidth < targetWidth || bmpHeight < targetHeight) {
            Serial.println("Error: Image is too small for the display!");
            return;
        }

        int rowSize = ((bmpWidth * bitDepth + 31) / 32) * 4;
        uint8_t *rowBuffer = (uint8_t*) malloc(rowSize);
        if (!rowBuffer) {
            Serial.println("Error: Not enough memory to allocate row buffer!");
            return;
        }

        float scaleX = (float)bmpWidth / targetWidth;
        float scaleY = (float)bmpHeight / targetHeight;
        int lastReadRow = -1;

        for (int y = 0; y < targetHeight; y++) {
            int bmpY = min((int)(y * scaleY), bmpHeight - 1);

            // Skip rows if needed
            for (int rowToSkip = lastReadRow + 1; rowToSkip < bmpY; rowToSkip++) {
                stream->readBytes(rowBuffer, rowSize);
            }

            // Read row
            stream->readBytes(rowBuffer, rowSize);

            for (int x = 0; x < targetWidth; x++) {
                int bmpX = min((int)(x * scaleX), bmpWidth - 1);
                int newX, newY;
                if (rotate90) {
                    newX = y;
                    newY = targetWidth - x - 1;
                } else {
                    newX = x;
                    newY = y;
                }
                uint32_t color = extractColor(rowBuffer, bmpWidth-bmpX, bitDepth);
                display->setPixel(newX, newY, (uint8_t*)&color);
            }
            lastReadRow = bmpY;

        }
        free(rowBuffer);
    } else {
        Serial.print("Failed to fetch image, error: ");
        Serial.println(httpCode);
    }
    http.end();
}

#endif // IMAGE_FETCH_DECODE_H

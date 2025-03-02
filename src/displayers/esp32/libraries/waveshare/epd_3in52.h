#ifndef EPD_3IN52_H
#define EPD_3IN52_H

#include  <display_handler.h>
#include "DEV_Config.h"
#include "EPD.h"

class EPD_3IN52 : public DisplayHandler {
public:
    EPD_3IN52() {}
    void init() override {
        DEV_Module_Init();
        EPD_3IN52_Init();
    }
    void clear() override {
        memset(imageBuffer, 0xFF, sizeof(imageBuffer));
        EPD_3IN52_Clear();
    }
    void update() override {
        EPD_3IN52_display(getBuffer());
        EPD_3IN52_refresh();
        Serial.println("Display updated!");
    }
    int getWidth() override { return 240; }
    int getHeight() override { return 360; }
    uint8_t* getBuffer() override { return imageBuffer; }
    int getSupportedBitDepth() override { return 1; }
    void setPixel(int x, int y, uint8_t* p_color) override {
        uint8_t color = *p_color;
        int byteIndex = (y * (getWidth() / 8)) + (x / 8);
        int bitIndex = 7 - (x % 8);
        if (color == 0) { // Black
            imageBuffer[byteIndex] &= ~(1 << bitIndex);
        } else { // White
            imageBuffer[byteIndex] |= (1 << bitIndex);
        }
    }

private:
    uint8_t imageBuffer[240 * 360 / 8] = {0xFF};
};

#endif // EPD_3IN52_H

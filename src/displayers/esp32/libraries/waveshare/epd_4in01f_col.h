#ifndef EPD_4IN01F__COL_H
#define EPD_4IN01F__COL_H

#include  <display_handler.h>
#include "DEV_Config.h"
#include "EPD.h"

class EPD_4IN01F_Displayer : public DisplayHandler {
public:
    EPD_4IN01F_Displayer() {}
    void init() override {
        DEV_Module_Init();
        EPD_4IN01F_Init();
        DEV_Delay_ms(100);
    }

    void clear() override {
        EPD_4IN01F_Clear(EPD_4IN01F_WHITE);
        EPD_SendCommand(0x61);//Set Resolution setting
        EPD_SendData(0x02);
        EPD_SendData(0x80);
        EPD_SendData(0x01);
        EPD_SendData(0x90);
        EPD_SendCommand(0x10);
    }

    void update() override {
        EPD_SendCommand(0x04);//0x04
        EPD_BusyHigh();
        EPD_SendCommand(0x12);//0x12
        EPD_BusyHigh();
        EPD_SendCommand(0x02);  //0x02
        EPD_BusyLow();
        DEV_Delay_ms(200);

        Serial.println("Display updated!");
    }
    int getWidth() override { return EPD_4IN01F_WIDTH; }
    int getHeight() override { return EPD_4IN01F_HEIGHT; }
    uint8_t* getBuffer() override { return NULL; }
    int getSupportedBitDepth() override { return 32; }
    void setPixel(int x, int y, uint8_t* p_color) override {
        // interpret color as ARGB
        uint32_t color = *(uint32_t*)p_color;
\
        // Convert RGB to 4-bit color
        uint8_t epdColor = rgb_to_4bit(color);
        int bitIndex = x % 2 == 0 ? 4 : 0;
        m_two_pixels |= (epdColor << bitIndex);
        if (x % 2 == 1) {
            // Write the two pixels to the buffer
            EPD_SendData(m_two_pixels);
            m_two_pixels = 0x00;
        }
    }

private:
    // Buffer for two pixels
    uint8_t m_two_pixels = 0x00;

    // Define the available colors in ARGB format (Alpha is ignored in the comparison)
    typedef struct {
        uint8_t r, g, b;
        uint8_t epd_color;
    } Color;

    static const uint8_t color_count =  7;
    static constexpr Color available_colors[color_count] = {
        {255, 255, 255, EPD_4IN01F_WHITE},  // White
        {70, 70, 70, EPD_4IN01F_BLACK},     // Black
        {0, 255, 0, EPD_4IN01F_GREEN},      // Green
        {0, 0, 255, EPD_4IN01F_BLUE},       // Blue
        {255, 0, 0, EPD_4IN01F_RED},        // Red
        {255, 128, 0, EPD_4IN01F_ORANGE},   // Orange
        {255, 255, 0, EPD_4IN01F_YELLOW}    // Yellow
    };

    // Function to find the closest color
    static uint8_t rgb_to_4bit(uint32_t bgra) {
        // Extract the RGBA little-endian values
        uint8_t a, r, g, b;
        a = (bgra >> 24) & 0xFF;
        r = (bgra >> 16) & 0xFF;
        g = (bgra >> 8) & 0xFF;
        b = bgra & 0xFF;

        int min_distance = 255 * 255 * 3; // Maximum possible distance in RGB space
        uint8_t closest_name = EPD_4IN01F_CLEAN;

        for (size_t i = 0; i < color_count; i++) {
            int dr = r - available_colors[i].r;
            int dg = g - available_colors[i].g;
            int db = b - available_colors[i].b;
            int distance = dr * dr + dg * dg + db * db;

            if (distance < min_distance) {
                min_distance = distance;
                closest_name = available_colors[i].epd_color;
            }
        }

        return closest_name;
    }


    static void EPD_SendCommand(UBYTE Reg)
    {
        DEV_Digital_Write(EPD_DC_PIN, 0);
        DEV_Digital_Write(EPD_CS_PIN, 0);
        DEV_SPI_WriteByte(Reg);
        DEV_Digital_Write(EPD_CS_PIN, 1);
    }
    static void EPD_SendData(UBYTE Data)
    {
        DEV_Digital_Write(EPD_DC_PIN, 1);
        DEV_Digital_Write(EPD_CS_PIN, 0);
        DEV_SPI_WriteByte(Data);
        DEV_Digital_Write(EPD_CS_PIN, 1);
    }
    static void EPD_BusyHigh(void)// If BUSYN=0 then waiting
    {
        while(!(DEV_Digital_Read(EPD_BUSY_PIN)));
    }

    static void EPD_BusyLow(void)// If BUSYN=1 then waiting
    {
        while(DEV_Digital_Read(EPD_BUSY_PIN));
    }
};

#endif // EPD_4IN01F__COL_H

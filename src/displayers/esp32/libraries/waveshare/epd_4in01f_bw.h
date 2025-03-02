#ifndef EPD_4IN01F_BW_H
#define EPD_4IN01F_BW_H

#include  <display_handler.h>
#include "DEV_Config.h"
#include "EPD.h"

class EPD_4IN01F_BW_Displayer : public DisplayHandler {
public:
    EPD_4IN01F_BW_Displayer() {}
    void init() override {
        DEV_Module_Init();
        EPD_4IN01F_Init();
        DEV_Delay_ms(100);
    }

    void clear() override {
        memset(imageBuffer, 0xFF, sizeof(imageBuffer));
    }

    void update() override {
        // cannot use EPD_4IN01F_Display because it uses 4-bit color
        // and it would require too much memory to convert the buffer

        EPD_SendCommand(0x61);//Set Resolution setting
        EPD_SendData(0x02);
        EPD_SendData(0x80);
        EPD_SendData(0x01);
        EPD_SendData(0x90);
        EPD_SendCommand(0x10);
        for(int i=0; i<EPD_4IN01F_HEIGHT; i++) {
            for(int j=0; j<EPD_4IN01F_WIDTH; j+=2) {
                int buffer_byteIndex = (i * (getWidth() / 8)) + (j / 8);
                uint8_t byte_data = imageBuffer[buffer_byteIndex];
                int  bitIndex = 7 - (j % 8);
                int  secondBitIndex = 7 - ((j + 1) % 8);
                uint8_t first_color =  (byte_data & (1 << bitIndex)) ? EPD_4IN01F_BLACK : EPD_4IN01F_WHITE;
                uint8_t second_color = (byte_data & (1 << (secondBitIndex))) ? EPD_4IN01F_BLACK : EPD_4IN01F_WHITE;
                EPD_SendData((first_color<<4)|second_color);
            }
        }
        EPD_SendCommand(0x04);//0x04
        EPD_BusyHigh();
        EPD_SendCommand(0x12);//0x12
        EPD_BusyHigh();
        EPD_SendCommand(0x02);  //0x02
        EPD_BusyLow();
        EPD_4IN01F_Sleep();
        DEV_Delay_ms(200);
        Serial.println("Display updated!");
    }
    int getWidth() override { return EPD_4IN01F_WIDTH; }
    int getHeight() override { return EPD_4IN01F_HEIGHT; }
    uint8_t* getBuffer() override { return imageBuffer; }
    int getSupportedBitDepth() override { return 1; }
    void setPixel(int x, int y, uint8_t* p_color) override {
        uint8_t color = *p_color;
        int byteIndex = (y * (getWidth() / 8)) + (x / 8);
        int bitIndex = 7 - (x % 8);
        if (color == 1) { // Black
            imageBuffer[byteIndex] &= ~(1 << bitIndex);
        } else { // White
            imageBuffer[byteIndex] |= (1 << bitIndex);
        }
    }

private:
    void EPD_SendCommand(UBYTE Reg)
    {
        DEV_Digital_Write(EPD_DC_PIN, 0);
        DEV_Digital_Write(EPD_CS_PIN, 0);
        DEV_SPI_WriteByte(Reg);
        DEV_Digital_Write(EPD_CS_PIN, 1);
    }
    void EPD_SendData(UBYTE Data)
    {
        DEV_Digital_Write(EPD_DC_PIN, 1);
        DEV_Digital_Write(EPD_CS_PIN, 0);
        DEV_SPI_WriteByte(Data);
        DEV_Digital_Write(EPD_CS_PIN, 1);
    }
    void EPD_BusyHigh(void)// If BUSYN=0 then waiting
    {
        while(!(DEV_Digital_Read(EPD_BUSY_PIN)));
    }

    void EPD_BusyLow(void)// If BUSYN=1 then waiting
    {
        while(DEV_Digital_Read(EPD_BUSY_PIN));
    }

    uint8_t imageBuffer[EPD_4IN01F_WIDTH * EPD_4IN01F_HEIGHT / 8] = {0xFF};
};

#endif // EPD_4IN01F_BW_H

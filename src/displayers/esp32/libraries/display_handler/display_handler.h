#ifndef DISPLAY_HANDLER_H
#define DISPLAY_HANDLER_H

#include <stdint.h>

class DisplayHandler {
public:
    virtual void init() = 0;
    virtual void update() = 0;
    virtual int getWidth() = 0;
    virtual int getHeight() = 0;
    virtual void clear() = 0;
    virtual uint8_t* getBuffer() = 0;
    virtual void setPixel(int x, int y, uint8_t* p_color) = 0;
    virtual int getSupportedBitDepth() = 0;
    virtual bool supportsRotation() { return true; }
    virtual ~DisplayHandler() {}
};

#endif // DISPLAY_HANDLER_H

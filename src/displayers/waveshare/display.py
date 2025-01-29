#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import os
import sys
import time

import numpy as np
from PIL import Image

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Image dimensions (height, width)
IMG_HW = (400, 640)

# Define label colors
LABEL_COLORS = [
    [255, 255, 255],  # white
    [255, 0, 0],  # red
    [0, 0, 255],  # blue
    [255, 255, 0],  # yellow
    [0, 255, 0],  # green
    [255, 128, 0],  # orange
    [70, 70, 70],  # black
]

# Quantize image to the closest colors
def closest(colors, image):
    """Quantize the image to the closest colors."""
    colors = np.array(colors).astype(np.int32)
    image = image.astype(np.int32)
    distances = np.argmin(np.array([np.sqrt(np.sum((color - image) ** 2, axis=2)) for color in colors]), axis=0)
    colors[-1, :] = np.array([0, 0, 0])  # Black for any unmatched pixels
    return colors[distances].astype(np.uint8)


# Display handler class
class DisplayHandler:
    def __init__(self, display_type, frame_path):
        """Initialize the display handler with the specified display type and frame path."""
        self.display_type = display_type
        self.frame_path = frame_path
        self.cached_moddate = -1

        # Initialize the appropriate display
        self.epaper = __import__("epaper")
        self.epd = self.epaper.epaper(display_type).EPD()

    def init_display(self):
        """Initialize and clear the display."""
        try:
            logging.info(f"Initializing display: {self.display_type}")
            self.epd.init()
            logging.info("Display initialized")
        except IOError as e:
            logging.error(f"IOError during initialization: {e}")
        except KeyboardInterrupt:
            self.cleanup()

    def cleanup(self):
        """Cleanup display resources."""
        logging.info("Exiting and cleaning up")
        if hasattr(self.epd, "module_exit"):
            self.epd.module_exit()
        exit()

    def refresh_display(self):
        """Refresh the display with the updated frame."""
        moddate = os.stat(self.frame_path).st_mtime
        if moddate != self.cached_moddate:
            self.cached_moddate = moddate
            try:
                logging.info("Clearing display")
                self.epd.Clear()
                logging.info("Loading image")
                Himage = Image.open(self.frame_path)
                logging.info("Quantizing image")
                quantised = closest(LABEL_COLORS, np.array(Himage))
                logging.info("Displaying image")
                img = Image.fromarray(quantised)
                # transpose image
                img = img.transpose(Image.ROTATE_180)
                self.epd.display(self.epd.getbuffer(img))
                print("Refreshed:", time.ctime(moddate))
            except IOError as e:
                logging.error(f"IOError during display refresh: {e}")
            except KeyboardInterrupt:
                self.cleanup()
        else:
            time.sleep(10)


# Main function
def main(display_type, frame_path):
    handler = DisplayHandler(display_type, frame_path)
    handler.init_display()
    try:
        while True:
            handler.refresh_display()
    except KeyboardInterrupt:
        handler.cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python display.py <display_type> <frame_path>")
        sys.exit(1)

    display_type_arg = sys.argv[1]
    frame_path_arg = sys.argv[2]

    if not os.path.exists(frame_path_arg):
        print(f"Error: Frame path does not exist: {frame_path_arg}")
        sys.exit(1)

    main(display_type_arg, frame_path_arg)

#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import os
import sys
import time

from PIL import Image

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Display handler class
class LCDDisplayHandler:
    def __init__(self, frame_path):
        """Initialize the display handler with the frame path."""
        self.frame_path = frame_path
        self.cached_moddate = -1

    def init_display(self):
        """Initialize the display."""
        logging.info("Initializing LCD display")
        # Clear previous images
        os.system("sudo fbi -T 1 -noverbose -a /dev/zero")

    def refresh_display(self):
        """Refresh the display with the updated frame."""
        moddate = os.stat(self.frame_path).st_mtime
        if moddate != self.cached_moddate:
            self.cached_moddate = moddate
            try:
                logging.info("Loading image")
                Himage = Image.open(self.frame_path)

                # Optionally rotate if needed
                Himage = Himage.rotate(0)  # Change this to 90, 180, or 270 if needed

                # Save the temporary image
                temp_image_path = "/tmp/lcd_display.bmp"
                Himage.save(temp_image_path)

                # Use fbi to display the image on the screen
                logging.info("Displaying image on LCD")
                os.system(f"sudo fbi -T 1 -noverbose -a {temp_image_path}")

                print("Refreshed:", time.ctime(moddate))
            except IOError as e:
                logging.error(f"IOError during display refresh: {e}")
            except KeyboardInterrupt:
                self.cleanup()
        else:
            time.sleep(5)  # Check for updates every 5 seconds

    def cleanup(self):
        """Cleanup display resources."""
        logging.info("Exiting and cleaning up")
        os.system("sudo pkill fbi")  # Kill fbi process
        exit()


# Main function
def main(frame_path):
    handler = LCDDisplayHandler(frame_path)
    handler.init_display()
    try:
        while True:
            handler.refresh_display()
    except KeyboardInterrupt:
        handler.cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lcd_display.py <frame_path>")
        sys.exit(1)

    frame_path_arg = sys.argv[1]

    if not os.path.exists(frame_path_arg):
        print(f"Error: Frame path does not exist: {frame_path_arg}")
        sys.exit(1)

    main(frame_path_arg)

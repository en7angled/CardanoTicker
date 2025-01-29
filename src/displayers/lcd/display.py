#!/usr/bin/python
# -*- coding:utf-8 -*-
import logging
import os
import sys
import time

from PIL import Image

# Initialize logging
logging.basicConfig(level=logging.INFO)


class LCDDisplayHandler:
    def __init__(self, frame_path, lcd_width, lcd_height, flip=False):
        """Initialize the display handler with the frame path and LCD resolution."""
        self.frame_path = frame_path
        self.lcd_width = lcd_width
        self.lcd_height = lcd_height
        self.cached_moddate = -1
        self.flip = flip

        # Ensure previous fbi processes are killed to avoid conflicts
        os.system("sudo pkill fbi")

    def init_display(self):
        """Initialize the display."""
        logging.info("Initializing LCD display")
        os.system(f"sudo fbi -T 1 -d /dev/fb0 -noverbose -a {self.frame_path} &")

    def refresh_display(self):
        """Refresh the display with the updated frame."""
        moddate = os.stat(self.frame_path).st_mtime
        if moddate != self.cached_moddate:
            self.cached_moddate = moddate
            try:
                logging.info("Loading image")
                Himage = Image.open(self.frame_path)

                # Ensure proper rotation (avoiding cropping)
                rot = -90 if self.flip else 90
                Himage = Himage.rotate(rot, expand=True)  # Rotate and expand

                # Resize image to fit LCD while preserving aspect ratio
                Himage.thumbnail((self.lcd_width, self.lcd_height), Image.LANCZOS)

                # Save the temporary image
                temp_image_path = "/tmp/lcd_display.bmp"
                Himage.save(temp_image_path)

                # Kill any existing fbi process to refresh properly
                os.system("sudo pkill fbi")

                # Use fbi to display the image persistently (fullscreen auto-scale)
                logging.info(f"Displaying image on LCD ({self.lcd_width}x{self.lcd_height})")
                os.system(f"sudo fbi -T 1 -d /dev/fb0 -noverbose -a {temp_image_path} &")

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
        os.system("sudo pkill fbi")  # Kill fbi process before exiting
        exit()


# Main function
def main(frame_path, lcd_width, lcd_height, flip=False):
    handler = LCDDisplayHandler(frame_path, lcd_width, lcd_height, flip=flip)
    handler.init_display()
    try:
        while True:
            handler.refresh_display()
    except KeyboardInterrupt:
        handler.cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python lcd_display.py <frame_path> <lcd_width> <lcd_height>")
        sys.exit(1)

    frame_path_arg = sys.argv[1]
    lcd_width_arg = int(sys.argv[2])
    lcd_height_arg = int(sys.argv[3])
    flip_arg = False
    if len(sys.argv) == 5:
        flip_arg = sys.argv[4].lower()
        if flip_arg == "true":
            flip_arg = True

    if not os.path.exists(frame_path_arg):
        print(f"Error: Frame path does not exist: {frame_path_arg}")
        sys.exit(1)

    main(frame_path_arg, lcd_width_arg, lcd_height_arg, flip_arg)

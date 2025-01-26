
#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
print(picdir)

import logging
import time
from PIL import Image
import numpy as np

import epaper

IMG_HW = (400,640)

#Simply what the name says.. 
label_colors = [

    [255, 255, 255], # white
    [255, 0, 0],     # red
    [0, 0, 255],     # blue
    [255, 255, 0],   # yellow
    [0, 255, 0],     # green
    [255, 128, 0],   # orange
    [70, 70, 70],    # black
]

# Quantize image
def closest(colors, image):
    #Converts elements into int32 
    colors = np.array(colors).astype(np.int32)
    image = image.astype(np.int32)
    #Finds Euclidean distance between each pixel in the image and the colors in the label_colors list
    distances = np.argmin(np.array([np.sqrt(np.sum((color - image) ** 2, axis=2)) for color in colors]), axis=0)
    colors[-1,:] = np.array([0,0,0])
    return colors[distances].astype(np.uint8)


logging.basicConfig(level=logging.DEBUG)
frame_path = os.path.join(picdir, 'frame.bmp')
cached_moddate =  -1

try:
    logging.info("E-Frame client")
    epd = epaper.epaper('epd4in01f').EPD()

    logging.info("init and Clear")
    epd.init()

except IOError as e:
    logging.info(e)
    
except KeyboardInterrupt:    
    logging.info("ctrl + c:")


while True:
    moddate = os.stat(frame_path)[8]
    if moddate != cached_moddate:
        cached_moddate = moddate
        try:
            epd.Clear()
            Himage = Image.open(frame_path)
            quantised = closest(label_colors, np.array(Himage))
            epd.display(epd.getbuffer(Image.fromarray(quantised)))
            print("refreshed: ", time.ctime(moddate))

        except IOError as e:
            logging.info(e)
            
        except KeyboardInterrupt:    
            logging.info("ctrl + c:")
            epd4in01f.epdconfig.module_exit()
            exit()
    else:
        time.sleep(10)

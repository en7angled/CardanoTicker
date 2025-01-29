import logging
import struct
from enum import Enum


class DashboardCommand(Enum):
    """
    Enum to represent the commands that can be sent to the dashboard manager
    """

    LOAD_DASHBOARD = "load_dashboard"
    GET_LAST_IMAGE = "get_last_image"
    GET_IMAGE_HASH = "get_image_hash"


class DashboardResponses(Enum):
    """
    Enum to represent the responses that can be sent by the dashboard manager
    """

    DASHBOARD_LOADED = "Dashboard loaded\n"
    INVALID_ARGUMENTS = "Invalid number of arguments\n"
    ERROR_CREATING_DASHBOARD = "Error creating dashboard\n"
    UNKNOWN_COMMAND = "Unknown command\n"

    @staticmethod
    def get_image_response(image):
        """
        Get the response for sending an image
        Args:
            image: The image to send
        """
        img = image
        img = img.convert("RGB")
        img_bytes = img.tobytes()
        img_size = len(img_bytes)
        width, height = img.size
        logging.info(f"Sending image of size {img_size} with width {width} and height {height}")
        return struct.pack('!II', width, height), struct.pack('!I', img_size), img_bytes

    @staticmethod
    def get_image_hash_response(image_hash):
        """
        Get the response for sending an image hash
        Args:
            image_hash: The image hash to send
        """
        return image_hash.encode() + b"\n"

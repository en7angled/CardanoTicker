from enum import Enum
from typing import Tuple


class Colors(Enum):
    green = (0, 255, 0)
    white = (255, 255, 255)
    orange = (255, 128, 0)
    blue = (0, 0, 200)
    light_blue = (0, 128, 255)
    black = (0, 0, 0)
    red = (255, 0, 0)
    gray = (128, 128, 128)
    yellow = (255, 255, 0)
    purple = (128, 0, 128)

    @staticmethod
    def from_string(color: str) -> Tuple[int, int, int]:
        """
        Get the color from a string
        Args:
            color: The color as a string
        """
        if color == "green":
            return Colors.green.value
        elif color == "white":
            return Colors.white.value
        elif color == "orange":
            return Colors.orange.value
        elif color == "blue":
            return Colors.blue.value
        elif color == "light_blue":
            return Colors.light_blue.value
        elif color == "black":
            return Colors.black.value
        elif color == "red":
            return Colors.red.value
        elif color == "gray":
            return Colors.gray.value
        elif color == "yellow":
            return Colors.yellow.value
        elif color == "purple":
            return Colors.purple.value
        else:
            return None

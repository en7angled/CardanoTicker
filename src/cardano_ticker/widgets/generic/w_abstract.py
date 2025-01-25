from typing import Tuple

from PIL import Image, ImageColor

from cardano_ticker.utils.colors import Colors


class AbstractWidget:
    def __init__(self, size: Tuple[int, int], background_color="white"):
        """
        Initialize the widget
        Args:
            aspect_ratio: The aspect ratio of the widget
            size: The size of the widget in pixels, (width, height)
        """

        self._size = size
        self.background_color = self._convert_color(background_color)
        self._canvas = Image.new("RGBA", self.resolution, self.background_color)

    def _normalize_color(self, color):
        return tuple(c / 255 for c in color)

    def _convert_color(self, color) -> Tuple[int, int, int]:
        """
        Convert the color to an RGB tuple
        Args:
            color: The color to convert
        """
        if isinstance(color, str):
            # check if color is a predefined color
            col = Colors.from_string(color)
            if col is not None:
                return col
            else:
                # convert color to RGB tuple using PIL
                return ImageColor.getrgb(color)
        else:
            # convert color to int if tuple contains normalized values
            return tuple([int(255 * c) if c <= 1 else c for c in color])

    def update(self, *args, **kwargs):
        """
        Update the widget

        """
        raise NotImplementedError("Subclasses must implement the update method")

    def render(self):
        """
        Render the widget as an image
        """
        raise NotImplementedError("Subclasses must implement the render method")

    @property
    def resolution(self) -> Tuple[int, int]:
        """
        Get the resolution of the widget
        """
        return (self.width, self.height)

    @property
    def width(self) -> int:
        """
        Get the width of the widget
        """
        return int(self._size[0])

    @property
    def height(self) -> int:
        """
        Get the height of the widget
        """
        return int(self._size[1])

    def get(self) -> Image.Image:
        """
        Get the image of the widget
        """
        return self._canvas

    def display(self):
        """
        Display the widget
        """
        self._canvas.show()


class ImageWidget(AbstractWidget):
    def __init__(self, size: Tuple[int, int], image: Image.Image):
        """
        Initialize the widget
        Args:
            size: The size of the widget in pixels, (width, height)
            image: The image to display
        """
        super().__init__(size)
        self._image = image

    def render(self):
        """
        Render the widget
        """
        self._canvas = self._image.resize(self.resolution)

    def update(self, image: Image.Image):
        """
        Update the image
        Args:
            image: The image to display
        """
        self._image = image
        self.render()

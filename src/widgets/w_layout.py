from typing import Tuple

import numpy as np
from PIL import Image, ImageColor

from src.widgets.generic.w_abstract import AbstractWidget


class WidgetLayout:
    def __init__(self, grid_size: Tuple[int, int], background_color: str = "white"):
        """
        Initialize the layout
        Args:
            grid_size: The size of the grid
            pixel_density: The pixel density of the pixels per unit length
        """
        self._widgets = []
        self.background_color = self._convert_color(background_color)

        self.resolution = grid_size
        self._canvas = Image.new("RGBA", self.resolution, self.background_color)
        self.grid_mask = np.zeros(self.resolution)

    def _convert_color(self, color) -> Tuple[int, int, int]:
        """
        Convert the color to an RGB tuple
        Args:
            color: The color to convert
        """
        if isinstance(color, str):
            return ImageColor.getrgb(color)
        else:
            # convert color to int if tuple contains normalized values
            return tuple([int(255 * c) if c <= 1 else c for c in color])

    def add_widget(self, widget: AbstractWidget, position: Tuple[int, int]):
        """
        Add a widget to the layout
        Args:
            widget: The widget to add
            position: The position of the widget in the grid
        """

        # check if widget is overlapping occupied grid
        tl = position
        br = (
            int(position[0] + widget.resolution[0]),
            int(position[1] + widget.resolution[1]),
        )
        if self.grid_mask[tl[0] : br[0], tl[1] : br[1]].any():
            print("Widget overlaps with another widget")
            return None

        self.grid_mask[tl[0] : br[0], tl[1] : br[1]] = 1
        self._widgets.append((widget, position))

    def remove_widget(self, widget: AbstractWidget):
        """
        Remove a widget from the layout
        Args:
            widget: The widget to remove
        """
        for w, pos in self._widgets:
            if w == widget:
                tl = pos
                br = (int(pos[0] + w.resolution[0]), int(pos[1] + w.resolution[1]))
                self.grid_mask[tl[0] : br[0], tl[1] : br[1]] = 0
                self._widgets.remove((w, pos))
                return True

        print("Widget not found")
        return False

    def render(self):
        """
        Render the layout
        """
        self._canvas = Image.new("RGBA", self.resolution, self.background_color)
        for widget, position in self._widgets:
            widget.update()
            widget.render()
            widget_img = widget.get()
            # rescale image to layout units
            widget_size = (widget.resolution[0], widget.resolution[1])

            widget_img = widget_img.resize((int(widget_size[0]), int(widget_size[1])))
            self._canvas.paste(widget_img, (position[0], position[1]))
        return self._canvas

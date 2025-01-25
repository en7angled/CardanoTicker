import os
from datetime import datetime
from typing import List, Tuple

from PIL import Image, ImageColor, ImageDraw, ImageFont

from cardano_ticker.utils.colors import Colors
from cardano_ticker.utils.constants import RESOURCES_DIR
from cardano_ticker.widgets.generic.w_abstract import AbstractWidget


class GenericTextWidget(AbstractWidget):
    def __init__(
        self,
        text,
        size: Tuple[int, int],
        text_color=Colors.black.value,
        background_color=Colors.white.value,
        auto_adjust_font=True,
    ):
        """
        Initialize the widget
        Args:
            price: The price of the Coin
        """
        super().__init__(size, background_color=background_color)
        # Load the font
        self.font_path = os.path.join(RESOURCES_DIR, "fonts/MerriweatherSans-VariableFont_wght.ttf")

        self.__load_font(size=self.height // 2)

        self._padding = 5
        self._text = text
        self._text_color = self._convert_color(text_color)

        self._auto_adjust_font = auto_adjust_font
        if self._auto_adjust_font:
            self.font = self.__load_adjusted_font(self._text, self.font, self.width)

    def __load_adjusted_font(self, text, font, width):
        """
        Adjust the font size to fit the text within the width
        Args:
            text: The text to fit
            font: The font to use
            width: The width to fit the text in
        """
        while font.getbbox(text)[2] > width:
            font.size -= 1
            font = ImageFont.truetype(self.font_path, font.size)
        return font

    def update(self):
        """
        Update the text
        Args:
            text: The text to be displayed
        """
        self.render()

    def set_text(self, text):
        """
        Set the text to be displayed
        Args:
            text: The text to be displayed
        """
        self._text = text

    def __load_font(self, size):
        """
        Load the font
        """
        self.font_size = size
        self.font = ImageFont.truetype(self.font_path, self.font_size)

    def render(self):
        """
        Render the widget
        """

        self._canvas = Image.new("RGBA", self.resolution, self.background_color)
        img_canvas = self._canvas
        draw = ImageDraw.Draw(img_canvas)

        # adjust the font size to fit the price
        if self._auto_adjust_font:
            self.font = self.__load_adjusted_font(self._text, self.font, self.width - self._padding)

        t_offset = (self.height - self.font_size) // 2
        draw.text((self._padding, t_offset), self._text, self._text_color, font=self.font)


class DateTimeWidget(GenericTextWidget):
    def __init__(
        self,
        size: Tuple[int, int],
        text_color=Colors.black.value,
        background_color=Colors.white.value,
    ):
        """
        Initialize the widget
        Args:
            price: The price of the Coin
        """
        time_txt = datetime.now().strftime("%b %d, %H:%M")

        super().__init__(time_txt, size, text_color=text_color, background_color=background_color)

    def update(self):
        """
        Update the text
        """
        time_txt = datetime.now().strftime("%b %d, %H:%M")
        self.set_text(time_txt)
        self.render()


class MutiTextWidget(AbstractWidget):
    """
    A widget to display multiple text parts, each with different font and color
    """

    def __init__(
        self,
        size: Tuple[int, int],
        text_parts: List[Tuple[str, ImageFont.ImageFont, str]],
        background_color: str = "white",
    ):
        super().__init__(size, background_color)
        self.text_parts = text_parts
        self.render()

    def update(self, text_parts: List[Tuple[str, ImageFont.ImageFont, str]]):
        self.text_parts = text_parts
        self.render()

    def render(self):
        draw = ImageDraw.Draw(self._canvas)
        x, y = 10, 10
        new_lines = ""
        for text, font, color in self.text_parts:
            starts_with_newline = text.startswith("\n")
            if starts_with_newline:
                new_lines += text[0]
                text = text[1:]
                x = 10

            draw.text((x, y), new_lines + text, font=font, fill=color)
            x += font.getbbox(text)[2]

    def _convert_color(self, color):
        if isinstance(color, tuple):
            return color
        return ImageColor.getrgb(color)

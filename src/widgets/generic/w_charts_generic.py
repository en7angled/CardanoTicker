from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, List

from src.widgets.generic.w_abstract import AbstractWidget
from src.utils.constants import RESOURCES_DIR

import io
import os
import matplotlib.pyplot as plt


class BarChartWidget(AbstractWidget):
    """
    Bar chart widget that displays a bar chart with the given data
    Colors can be specified
    """

    def __init__(
        self,
        size: Tuple[int, int],
        data: List[Tuple[str, int]],
        colors,
        title: str = None,
        background_color="white",
        font_size: int = 22,
    ):
        super().__init__(size, background_color=background_color)
        self.data = data
        self.colors = [self._convert_color(color) for color in colors]
        # convert colors from uint8 to float
        self.colors = [self._normalize_color(color) for color in self.colors]
        self.font_size = font_size

        self.title = title
        self.render()

    def update(self, data: List[Tuple[str, int]], colors: List[str]):
        self.data = data
        self.colors = [self._convert_color(color) for color in colors]
        # convert colors from uint8 to float
        self.colors = [self._normalize_color(color) for color in self.colors]
        self.render()

    def render(self):
        if len(self.data) == 0:
            return

        # font size bigger
        plt.rcParams.update({"font.size": self.font_size})

        labels, values = zip(*self.data)
        fig, ax = plt.subplots(figsize=(self.width / 100, self.height / 100))
        # make figure larger to fit the labels
        fig.subplots_adjust(left=0.2, right=0.8, top=0.8, bottom=0.2)

        bk = self._normalize_color(self.background_color)
        fig.set_facecolor(bk)
        # make ax background transparent
        ax.patch.set_alpha(0)
        ax.bar(labels, values, color=self.colors)
        ax.set_ylabel("Values")
        if self.title:
            ax.set_title(self.title)

        # fig.autofmt_xdate()
        fig.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        self._canvas = Image.open(buf).convert("RGBA")
        buf.close()
        plt.close(fig)


class PieChartWidget(AbstractWidget):
    """
    Pie chart widget that displays a pie chart with the given data
    Colors can be specified
    """

    def __init__(
        self,
        size: Tuple[int, int],
        data: List[Tuple[str, int]],
        colors: List[str],
        background_color: str = "white",
        font_size: int = 22,
    ):
        super().__init__(size, background_color=background_color)
        self.data = data
        self.colors = [self._convert_color(color) for color in colors]
        # convert colors from uint8 to float
        self.colors = [self._normalize_color(color) for color in self.colors]
        self.font_size = font_size
        self.render()

    def update(self, data: List[Tuple[str, int]], colors: List[str]):
        self.data = data
        self.colors = [self._convert_color(color) for color in colors]
        # convert colors from uint8 to float
        self.colors = [self._normalize_color(color) for color in self.colors]
        self.render()

    def render(self):
        if len(self.data) == 0:
            return
        # font size bigger
        plt.rcParams.update({"font.size": self.font_size})

        labels, values = zip(*self.data)
        fig, ax = plt.subplots(figsize=(self.width / 100, self.height / 100))
        fig.set_facecolor(self._normalize_color(self.background_color))
        ax.pie(
            values, labels=labels, colors=self.colors, autopct="%1.1f%%", startangle=90
        )
        ax.axis("equal")
        # set slice text color
        # plt.setp(ax.pie(values, labels=labels, colors=self.colors, autopct='%1.1f%%', startangle=90)[1], size=20, color='white')

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        self._canvas = Image.open(buf).convert("RGBA")
        buf.close()
        plt.close(fig)


class LineChartWidget(AbstractWidget):
    """
    Line chart widget that displays a line chart with the given data
    Colors can be specified
    """

    def __init__(
        self,
        size: Tuple[int, int],
        data: List[Tuple[str, List[int]]],
        colors: List[str],
        background_color: str = "white",
        font_size: int = 22,
        title: str = None,
    ):
        super().__init__(size, background_color=background_color)
        self.data = data
        self.colors = [self._convert_color(color) for color in colors]
        # convert colors from uint8 to float
        self.colors = [self._normalize_color(color) for color in self.colors]
        self.font_size = font_size
        self.title = title
        self.render()

    def update(self, data: List[Tuple[str, List[int]]], colors: List[str]):
        self.data = data
        self.colors = [self._convert_color(color) for color in colors]
        # convert colors from uint8 to float
        self.colors = [self._normalize_color(color) for color in self.colors]
        self.render()

    def render(self):
        if len(self.data) == 0:
            return

        # font size bigger
        plt.rcParams.update({"font.size": self.font_size})

        fig, ax = plt.subplots(figsize=(self.width / 100, self.height / 100))
        if self.title:
            ax.set_title(self.title)
            # set title color
            # ax.title.set_color("white")

        fig.set_facecolor(self._normalize_color(self.background_color))
        ax.patch.set_alpha(0)

        for idx, (label, values) in enumerate(self.data):
            ax.plot(values, label=label, color=self.colors[idx])

        # legend alpah to 0

        ax.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        self._canvas = Image.open(buf).convert("RGBA")
        buf.close()
        plt.close(fig)


# Create a progress bar widget
class ProgressBarWidget(AbstractWidget):
    def __init__(
        self,
        size,
        progress,
        text_color="white",
        background_color="gray",
        fill_color="green",
        font_size=20,
    ):
        super().__init__(size, background_color)
        self.progress = progress
        self.font_size = font_size
        self.font_path = os.path.join(RESOURCES_DIR, "fonts/DejaVuSans.ttf")
        self.text_color = self._convert_color(text_color)
        self.fill_color = self._convert_color(fill_color)
        if progress > 1.0:
            self.progress = self.progress / 100

    def render(self):
        # Create a new image with the given size and background color
        self._canvas = Image.new("RGBA", self.resolution, self.background_color)
        draw = ImageDraw.Draw(self._canvas)

        # Draw the progress bar
        progress_width = int(self.resolution[0] * self.progress)
        draw.rectangle([0, 0, progress_width, self.resolution[1]], fill=self.fill_color)

        # Draw the progress text
        font = ImageFont.truetype(self.font_path, self.font_size)
        text = f"{int(self.progress * 100)}%"
        text_width, text_height = draw.textsize(text, font)
        text_x = (self.resolution[0] - text_width) // 2
        text_y = (self.resolution[1] - text_height) // 2
        draw.text((text_x, text_y), text, font=font, fill=self.text_color)

        return self._canvas

    def update(self, progress):
        self.progress = progress
        if self.progress > 1.0:
            self.progress = self.progress / 100

        self.render()

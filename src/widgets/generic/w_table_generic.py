from typing import List, Tuple

from PIL import ImageColor, ImageDraw, ImageFont

from src.widgets.generic.w_abstract import AbstractWidget


class TableWidget(AbstractWidget):
    """
    Generic table widget, displays a table with headers and rows
    We can specify the orientation of the headers and rows , color of the headers and rows and the background color
    """

    def __init__(
        self,
        size: Tuple[int, int],
        headers: List[str],
        rows: List[List[str]],
        font: ImageFont.ImageFont,
        header_orientation: str = "columns",
        header_color: str = "black",
        row_color: str = "black",
        background_color: str = "white",
    ):
        super().__init__(size, background_color)
        self.headers = headers
        self.rows = rows
        self.font = font
        self.header_orientation = header_orientation
        self.header_color = ImageColor.getrgb(header_color)
        self.row_color = ImageColor.getrgb(row_color)
        self.render()

    def update(
        self,
        headers: List[str],
        rows: List[List[str]],
        header_orientation: str = "columns",
    ):
        self.headers = headers
        self.rows = rows
        self.header_orientation = header_orientation
        self.render()

    def render(self):

        if len(self.headers) == 0 or len(self.rows) == 0:
            return

        draw = ImageDraw.Draw(self._canvas)
        x, y = 10, 10
        header_widths = [
            max(
                self.font.getsize(header)[0],
                max(self.font.getsize(row[i])[0] for row in self.rows),
            )
            + 20
            for i, header in enumerate(self.headers)
        ]
        row_height = self.font.getsize(self.headers[0])[1] + 20

        if self.header_orientation == "columns":
            # Draw headers
            for i, header in enumerate(self.headers):
                draw.rectangle(
                    [x, y, x + header_widths[i], y + row_height],
                    outline="blue",
                    fill=self.background_color,
                )
                draw.text((x + 10, y + 10), header, font=self.font, fill=self.header_color)
                x += header_widths[i]
            y += row_height

            # Draw rows
            for row in self.rows:
                x = 10
                for i, cell in enumerate(row):
                    draw.rectangle(
                        [x, y, x + header_widths[i], y + row_height],
                        outline="blue",
                        fill=self.background_color,
                    )
                    draw.text((x + 10, y + 10), cell, font=self.font, fill=self.row_color)
                    x += header_widths[i]
                y += row_height

        else:
            max_header_width = max(header_widths)
            # Draw headers as rows
            for i, header in enumerate(self.headers):

                draw.rectangle(
                    [x, y, x + max_header_width, y + row_height],
                    outline="blue",
                    fill=self.background_color,
                )
                draw.text((x + 10, y + 10), header, font=self.font, fill=self.header_color)
                y += row_height

            # Draw rows as columns
            offset_x = max_header_width
            for i, row in enumerate(self.rows):
                x = 10 + offset_x
                row_width = max(self.font.getsize(cell)[0] for cell in row) + 20

                y = 10
                for j, cell in enumerate(row):
                    draw.rectangle(
                        [x, y, x + row_width, y + row_height],
                        outline="blue",
                        fill=self.background_color,
                    )
                    draw.text((x + 10, y + 10), cell, font=self.font, fill=self.row_color)
                    y += row_height
                offset_x += row_width

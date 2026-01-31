"""
Portfolio visualization widgets for e-ink displays.

Includes:
- AllocationDonutChart: Donut-style pie chart for portfolio allocation
- TreemapWidget: Treemap visualization for gains/losses heatmap
"""
import io
import logging
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

from cardano_ticker.widgets.generic.w_abstract import AbstractWidget
from cardano_ticker.data_fetcher.portfolio_fetcher import PortfolioDataFetcher, get_asset_color
from cardano_ticker.utils.constants import RESOURCES_DIR

logging.basicConfig(level=logging.INFO)


class AllocationDonutChart(AbstractWidget):
    """
    Donut-style pie chart showing portfolio allocation.
    Optimized for e-ink displays with clear labels and percentages.
    """

    def __init__(
        self,
        size: Tuple[int, int],
        data: Optional[List[Tuple[str, float, str]]] = None,
        portfolio_fetcher: Optional[PortfolioDataFetcher] = None,
        background_color: str = "white",
        text_color: str = "black",
        hole_ratio: float = 0.5,
        font_size: int = 10,
        show_legend: bool = True,
        title: Optional[str] = None,
    ):
        """
        Initialize the donut chart.

        Args:
            size: Widget size (width, height)
            data: List of (asset_name, value, color) tuples. If None, uses portfolio_fetcher.
            portfolio_fetcher: PortfolioDataFetcher instance to get live data
            background_color: Background color
            text_color: Text color for labels
            hole_ratio: Size of the center hole (0-1, where 0.5 = 50% hole)
            font_size: Font size for labels
            show_legend: Whether to show a legend
            title: Optional title for the chart
        """
        super().__init__(size, background_color=background_color)
        self.data = data or []
        self.portfolio_fetcher = portfolio_fetcher
        self.text_color = self._convert_color(text_color)
        self.text_color_normalized = self._normalize_color(self.text_color)
        self.hole_ratio = hole_ratio
        self.font_size = font_size
        self.show_legend = show_legend
        self.title = title

    def update(self, data: Optional[List[Tuple[str, float, str]]] = None):
        """Update the chart data"""
        if data is not None:
            self.data = data
        elif self.portfolio_fetcher:
            self.data = self.portfolio_fetcher.get_allocation_data(refresh=True)

    def render(self):
        """Render the donut chart"""
        if not self.data:
            self._render_empty()
            return

        # Filter out zero/negative values
        filtered_data = [(name, value, color) for name, value, color in self.data if value > 0]
        if not filtered_data:
            self._render_empty()
            return

        labels, values, colors = zip(*filtered_data)

        # Calculate percentages
        total = sum(values)
        percentages = [v / total * 100 for v in values]

        # Normalize colors for matplotlib
        norm_colors = [self._normalize_color(self._convert_color(c)) for c in colors]

        # Create figure
        fig_width = self.width / 100
        fig_height = self.height / 100
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        # Set background
        bk_color = self._normalize_color(self.background_color)
        fig.patch.set_facecolor(bk_color)
        ax.set_facecolor(bk_color)

        # Create custom labels with percentages
        display_labels = [f'{l}\n{p:.1f}%' for l, p in zip(labels, percentages)]

        # Draw pie chart with hole (donut)
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,  # We'll add legend instead
            colors=norm_colors,
            autopct='',
            startangle=90,
            wedgeprops={'width': 1 - self.hole_ratio, 'edgecolor': 'white', 'linewidth': 1},
            pctdistance=0.75,
        )

        # Add center text showing total value
        center_text = f'${total:,.0f}'
        ax.text(0, 0, center_text, ha='center', va='center',
                fontsize=self.font_size + 2, fontweight='bold',
                color=self.text_color_normalized)

        # Add legend if enabled
        if self.show_legend:
            legend_labels = [f'{l} ({p:.1f}%)' for l, p in zip(labels, percentages)]
            ax.legend(wedges, legend_labels, loc='center left', bbox_to_anchor=(1, 0.5),
                      fontsize=self.font_size - 2, frameon=False)
            fig.subplots_adjust(right=0.65)

        # Add title if provided
        if self.title:
            ax.set_title(self.title, fontsize=self.font_size, color=self.text_color_normalized, pad=10)

        ax.axis('equal')

        # Convert to image
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                    facecolor=bk_color, edgecolor='none')
        buf.seek(0)
        img = Image.open(buf).convert('RGBA')

        # Resize to target size
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        self._canvas = img

        buf.close()
        plt.close(fig)

    def _render_empty(self):
        """Render empty state"""
        self._canvas = Image.new('RGBA', self.resolution, self.background_color)
        draw = ImageDraw.Draw(self._canvas)
        font_path = os.path.join(RESOURCES_DIR, "fonts/DejaVuSans.ttf")
        try:
            font = ImageFont.truetype(font_path, self.font_size)
        except:
            font = ImageFont.load_default()

        text = "No allocation data"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2
        draw.text((x, y), text, fill=self.text_color, font=font)


class TreemapWidget(AbstractWidget):
    """
    Treemap visualization for portfolio gains/losses.
    Shows rectangles sized by absolute P&L, colored green (profit) or red (loss).
    Optimized for e-ink displays.
    """

    def __init__(
        self,
        size: Tuple[int, int],
        data: Optional[List[Tuple[str, float, str]]] = None,
        portfolio_fetcher: Optional[PortfolioDataFetcher] = None,
        background_color: str = "white",
        text_color: str = "white",
        font_size: int = 12,
        title: Optional[str] = None,
        padding: int = 2,
    ):
        """
        Initialize the treemap widget.

        Args:
            size: Widget size (width, height)
            data: List of (asset_name, pnl_value, color) tuples. If None, uses portfolio_fetcher.
            portfolio_fetcher: PortfolioDataFetcher instance to get live data
            background_color: Background color
            text_color: Text color for labels inside rectangles
            font_size: Font size for labels
            title: Optional title for the chart
            padding: Padding between rectangles in pixels
        """
        super().__init__(size, background_color=background_color)
        self.data = data or []
        self.portfolio_fetcher = portfolio_fetcher
        self.text_color = self._convert_color(text_color)
        self.font_size = font_size
        self.title = title
        self.padding = padding
        self.font_path = os.path.join(RESOURCES_DIR, "fonts/DejaVuSans.ttf")

    def update(self, data: Optional[List[Tuple[str, float, str]]] = None):
        """Update the treemap data"""
        if data is not None:
            self.data = data
        elif self.portfolio_fetcher:
            self.data = self.portfolio_fetcher.get_pnl_data(refresh=True)

    def _squarify(self, values: List[float], x: float, y: float, width: float, height: float) -> List[dict]:
        """
        Squarified treemap algorithm.
        Returns list of rectangles: [{'x': x, 'y': y, 'w': width, 'h': height, 'index': i}, ...]
        """
        if not values:
            return []

        total = sum(values)
        if total == 0:
            return []

        rectangles = []
        remaining_values = list(enumerate(values))

        def layout_row(indices_values, x, y, width, height, vertical):
            """Layout a row/column of rectangles"""
            total_val = sum(v for _, v in indices_values)
            if total_val == 0:
                return []

            rects = []
            if vertical:
                row_width = (total_val / sum(values)) * width if values else 0
                current_y = y
                for idx, val in indices_values:
                    rect_height = (val / total_val) * height if total_val > 0 else 0
                    rects.append({
                        'x': x, 'y': current_y,
                        'w': row_width, 'h': rect_height,
                        'index': idx
                    })
                    current_y += rect_height
            else:
                row_height = (total_val / sum(values)) * height if values else 0
                current_x = x
                for idx, val in indices_values:
                    rect_width = (val / total_val) * width if total_val > 0 else 0
                    rects.append({
                        'x': current_x, 'y': y,
                        'w': rect_width, 'h': row_height,
                        'index': idx
                    })
                    current_x += rect_width
            return rects

        # Simple squarify: split horizontally or vertically based on aspect ratio
        def squarify_recursive(indices_values, x, y, w, h):
            if not indices_values:
                return []
            if len(indices_values) == 1:
                idx, val = indices_values[0]
                return [{'x': x, 'y': y, 'w': w, 'h': h, 'index': idx}]

            total_val = sum(v for _, v in indices_values)
            if total_val == 0:
                return []

            # Find split point
            mid_val = total_val / 2
            cumsum = 0
            split_idx = 0
            for i, (_, v) in enumerate(indices_values):
                cumsum += v
                if cumsum >= mid_val:
                    split_idx = i + 1
                    break

            if split_idx == 0:
                split_idx = 1
            if split_idx >= len(indices_values):
                split_idx = len(indices_values) - 1

            left = indices_values[:split_idx]
            right = indices_values[split_idx:]

            left_sum = sum(v for _, v in left)
            ratio = left_sum / total_val if total_val > 0 else 0.5

            rects = []
            if w >= h:
                # Split vertically
                left_w = w * ratio
                rects.extend(squarify_recursive(left, x, y, left_w, h))
                rects.extend(squarify_recursive(right, x + left_w, y, w - left_w, h))
            else:
                # Split horizontally
                left_h = h * ratio
                rects.extend(squarify_recursive(left, x, y, w, left_h))
                rects.extend(squarify_recursive(right, x, y + left_h, w, h - left_h))

            return rects

        return squarify_recursive(remaining_values, x, y, width, height)

    def render(self):
        """Render the treemap"""
        if not self.data:
            self._render_empty()
            return

        # Filter and prepare data (use absolute values for sizing)
        filtered_data = [(name, pnl, color) for name, pnl, color in self.data if pnl != 0]
        if not filtered_data:
            self._render_empty()
            return

        # Create canvas
        self._canvas = Image.new('RGBA', self.resolution, self.background_color)
        draw = ImageDraw.Draw(self._canvas)

        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
            small_font = ImageFont.truetype(self.font_path, max(8, self.font_size - 4))
        except:
            font = ImageFont.load_default()
            small_font = font

        # Calculate title offset
        title_height = 0
        if self.title:
            title_bbox = draw.textbbox((0, 0), self.title, font=font)
            title_height = title_bbox[3] - title_bbox[1] + 10
            title_x = (self.width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, 5), self.title, fill=self._convert_color("black"), font=font)

        # Treemap area
        treemap_y = title_height
        treemap_height = self.height - title_height - self.padding

        # Prepare values (absolute for sizing)
        names = [d[0] for d in filtered_data]
        values = [abs(d[1]) for d in filtered_data]
        colors = [d[1] for d in filtered_data]  # Keep original for color determination

        # Calculate rectangles
        rectangles = self._squarify(
            values,
            self.padding,
            treemap_y + self.padding,
            self.width - 2 * self.padding,
            treemap_height - 2 * self.padding
        )

        # Draw rectangles
        for rect in rectangles:
            idx = rect['index']
            x, y, w, h = rect['x'], rect['y'], rect['w'], rect['h']

            # Apply padding
            x += self.padding / 2
            y += self.padding / 2
            w -= self.padding
            h -= self.padding

            if w <= 0 or h <= 0:
                continue

            # Determine color based on P&L sign
            pnl = filtered_data[idx][1]
            fill_color = '#16a34a' if pnl >= 0 else '#dc2626'

            # Draw rectangle
            draw.rectangle(
                [x, y, x + w, y + h],
                fill=fill_color,
                outline='white',
                width=1
            )

            # Draw label if rectangle is big enough
            name = names[idx]
            pnl_text = f'{"+" if pnl >= 0 else ""}${pnl:,.0f}'

            # Check if text fits
            name_bbox = draw.textbbox((0, 0), name, font=font)
            name_w = name_bbox[2] - name_bbox[0]
            name_h = name_bbox[3] - name_bbox[1]

            pnl_bbox = draw.textbbox((0, 0), pnl_text, font=small_font)
            pnl_w = pnl_bbox[2] - pnl_bbox[0]
            pnl_h = pnl_bbox[3] - pnl_bbox[1]

            text_color = 'white'

            if w > name_w + 10 and h > name_h + pnl_h + 10:
                # Both name and P&L fit
                text_x = x + (w - name_w) / 2
                text_y = y + (h - name_h - pnl_h) / 2
                draw.text((text_x, text_y), name, fill=text_color, font=font)

                pnl_x = x + (w - pnl_w) / 2
                pnl_y = text_y + name_h + 2
                draw.text((pnl_x, pnl_y), pnl_text, fill=text_color, font=small_font)

            elif w > name_w + 6 and h > name_h + 6:
                # Only name fits
                text_x = x + (w - name_w) / 2
                text_y = y + (h - name_h) / 2
                draw.text((text_x, text_y), name, fill=text_color, font=font)

            elif w > 20 and h > 15:
                # Try just asset symbol (first 3-4 chars)
                short_name = name[:4]
                short_bbox = draw.textbbox((0, 0), short_name, font=small_font)
                short_w = short_bbox[2] - short_bbox[0]
                short_h = short_bbox[3] - short_bbox[1]
                if w > short_w + 4 and h > short_h + 4:
                    text_x = x + (w - short_w) / 2
                    text_y = y + (h - short_h) / 2
                    draw.text((text_x, text_y), short_name, fill=text_color, font=small_font)

    def _render_empty(self):
        """Render empty state"""
        self._canvas = Image.new('RGBA', self.resolution, self.background_color)
        draw = ImageDraw.Draw(self._canvas)
        try:
            font = ImageFont.truetype(self.font_path, self.font_size)
        except:
            font = ImageFont.load_default()

        text = "No P&L data"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2
        draw.text((x, y), text, fill=self._convert_color("black"), font=font)

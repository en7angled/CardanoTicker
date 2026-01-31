"""
Portfolio visualization widgets for e-ink displays.

Includes:
- PortfolioSummaryWidget: Top bar with key portfolio metrics
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


class PortfolioSummaryWidget(AbstractWidget):
    """
    Summary widget showing key portfolio metrics:
    - Portfolio value in USD and BTC
    - Current BTC price
    - 7-day performance (if available)
    """

    def __init__(
        self,
        size: Tuple[int, int],
        portfolio_fetcher: Optional[PortfolioDataFetcher] = None,
        background_color: str = "#f8f9fa",
        text_color: str = "black",
        font_size: int = 14,
    ):
        super().__init__(size, background_color=background_color)
        self.portfolio_fetcher = portfolio_fetcher
        self.text_color = self._convert_color(text_color)
        self.font_size = font_size
        self.font_path = os.path.join(RESOURCES_DIR, "fonts/Roboto_Condensed-Black.ttf")
        self.font_path_regular = os.path.join(RESOURCES_DIR, "fonts/DejaVuSans.ttf")

        # Cached data
        self.total_value = 0
        self.btc_price = 0
        self.total_pnl = 0
        self.total_pnl_percent = 0
        self.perf_7d = None  # 7-day performance (if available)

    def update(self):
        """Fetch latest portfolio data"""
        if self.portfolio_fetcher:
            data = self.portfolio_fetcher.fetch_from_ticker_api()
            if data and 'summary' in data:
                summary = data['summary']
                self.total_value = summary.get('totalValue', 0)
                self.btc_price = summary.get('btcPrice', 0)
                self.total_pnl = summary.get('totalPnl', 0)
                self.total_pnl_percent = summary.get('totalPnlPercent', 0)
                self.perf_7d = summary.get('performance7d', None)

    def _auto_adjust_font(self, text, font_path, start_size, max_width):
        """Shrink font until text fits within max_width"""
        font = ImageFont.truetype(font_path, start_size)
        while font.getbbox(text)[2] > max_width and font.size > 8:
            font = ImageFont.truetype(font_path, font.size - 1)
        return font

    def render(self):
        """Render the summary bar optimized for 7-color e-ink display - 2 rows layout"""
        self._canvas = Image.new('RGBA', self.resolution, self.background_color)
        draw = ImageDraw.Draw(self._canvas)

        # E-ink 7-color palette - EXACT RGB values from display driver
        COLOR_BLACK = (70, 70, 70)
        COLOR_GREEN = (0, 255, 0)
        COLOR_BLUE = (0, 0, 255)
        COLOR_RED = (255, 0, 0)
        COLOR_ORANGE = (255, 128, 0)

        # Calculate BTC value
        btc_value = self.total_value / self.btc_price if self.btc_price > 0 else 0

        # Layout: 2 rows x 2 columns
        section_width = self.width // 2
        row_height = self.height // 2
        padding_x = 10

        # Calculate font sizes based on available space
        # Value font: fit within cell, start at row_height * 0.5
        value_font_size = int(row_height * 0.55)
        label_font_size = int(row_height * 0.30)

        try:
            font_bold = ImageFont.truetype(self.font_path, value_font_size)
            font_label = ImageFont.truetype(self.font_path_regular, label_font_size)
        except:
            font_bold = ImageFont.load_default()
            font_label = font_bold

        cell_width = section_width - padding_x * 2

        # Prepare all values
        usd_value = f"${self.total_value:,.0f}"
        btc_value_str = f"{btc_value:.3f} BTC"
        btc_price_str = f"${self.btc_price:,.0f}"

        if self.perf_7d is not None:
            perf_value = f"{'+' if self.perf_7d >= 0 else ''}{self.perf_7d:.1f}%"
            perf_color = COLOR_GREEN if self.perf_7d >= 0 else COLOR_RED
            perf_label = "7d Change"
        else:
            perf_value = f"{'+' if self.total_pnl >= 0 else ''}${self.total_pnl:,.0f}"
            perf_color = COLOR_GREEN if self.total_pnl >= 0 else COLOR_RED
            perf_label = "Total P&L"

        # Auto-adjust fonts for each value
        font_usd = self._auto_adjust_font(usd_value, self.font_path, value_font_size, cell_width)
        font_btc = self._auto_adjust_font(btc_value_str, self.font_path, value_font_size, cell_width)
        font_price = self._auto_adjust_font(btc_price_str, self.font_path, value_font_size, cell_width)
        font_pnl = self._auto_adjust_font(perf_value, self.font_path, value_font_size, cell_width)

        # Row positions
        label_y_offset = 2
        value_y_offset = label_font_size + 4
        col2_x = section_width

        # Row 1, Column 1: Portfolio Value (USD)
        draw.text((padding_x, label_y_offset), "Portfolio", fill=COLOR_BLACK, font=font_label)
        draw.text((padding_x, value_y_offset), usd_value, fill=COLOR_BLACK, font=font_usd)

        # Row 1, Column 2: Portfolio Value (BTC)
        draw.text((col2_x + padding_x, label_y_offset), "In BTC", fill=COLOR_BLACK, font=font_label)
        draw.text((col2_x + padding_x, value_y_offset), btc_value_str, fill=COLOR_ORANGE, font=font_btc)

        # Row 2
        row2_y = row_height

        # Row 2, Column 1: BTC Price
        draw.text((padding_x, row2_y + label_y_offset), "BTC Price", fill=COLOR_BLACK, font=font_label)
        draw.text((padding_x, row2_y + value_y_offset), btc_price_str, fill=COLOR_BLUE, font=font_price)

        # Row 2, Column 2: Total P&L
        draw.text((col2_x + padding_x, row2_y + label_y_offset), perf_label, fill=COLOR_BLACK, font=font_label)
        draw.text((col2_x + padding_x, row2_y + value_y_offset), perf_value, fill=perf_color, font=font_pnl)

        # Draw separating lines
        draw.line([(0, row_height), (self.width, row_height)], fill=COLOR_BLACK, width=1)
        draw.line([(section_width, 0), (section_width, self.height)], fill=COLOR_BLACK, width=1)
        draw.line([(0, self.height - 1), (self.width, self.height - 1)], fill=COLOR_BLACK, width=2)


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
        btc_price: Optional[float] = None,
        hide_value: bool = False,
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
            btc_price: Current BTC price in USD for displaying value in BTC
            hide_value: If True, don't show value in title (use when summary bar shows it)
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
        self.btc_price = btc_price
        self.hide_value = hide_value

    def update(self, data: Optional[List[Tuple[str, float, str]]] = None):
        """Update the chart data"""
        if data is not None:
            self.data = data
        elif self.portfolio_fetcher:
            raw_data = self.portfolio_fetcher.get_allocation_data(refresh=True)
            # Override with e-ink compatible colors
            self.data = [(name, value, get_asset_color(name)) for name, value, _ in raw_data]

    def render(self):
        """Render the donut chart - following PieChartWidget pattern"""
        if not self.data:
            self._render_empty()
            return

        # Filter out zero/negative values
        filtered_data = [(name, value, color) for name, value, color in self.data if value > 0]
        if not filtered_data:
            self._render_empty()
            return

        labels, values, colors = zip(*filtered_data)

        # Normalize colors for matplotlib
        norm_colors = [self._normalize_color(self._convert_color(c)) for c in colors]

        # Set font size in rcParams like other widgets do
        plt.rcParams.update({"font.size": self.font_size})

        # Create figure at exact widget size (like PieChartWidget)
        fig, ax = plt.subplots(figsize=(self.width / 100, self.height / 100))

        # Set background
        bk_color = self._normalize_color(self.background_color)
        fig.set_facecolor(bk_color)

        # Draw pie chart with labels directly on it (like PieChartWidget)
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=norm_colors,
            autopct='%1.0f%%',
            startangle=90,
            wedgeprops={'width': 1 - self.hole_ratio, 'edgecolor': 'white', 'linewidth': 1},
        )

        # Set text colors
        for text in texts:
            text.set_color(self.text_color_normalized)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(self.font_size - 2)

        ax.axis('equal')

        # Add title if specified
        if self.title:
            ax.set_title(self.title, fontsize=self.font_size + 2, fontweight='bold',
                         color=self.text_color_normalized)

        # Save figure (like PieChartWidget - no bbox_inches='tight')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor=bk_color)
        buf.seek(0)
        self._canvas = Image.open(buf).convert('RGBA')

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
    Treemap visualization for portfolio gains/losses or 7-day performance.
    Shows rectangles sized by absolute value, colored green (gain) or red (loss).
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
        show_7d: bool = False,
    ):
        """
        Initialize the treemap widget.

        Args:
            size: Widget size (width, height)
            data: List of (asset_name, value, color) tuples. If None, uses portfolio_fetcher.
            portfolio_fetcher: PortfolioDataFetcher instance to get live data
            background_color: Background color
            text_color: Text color for labels inside rectangles
            font_size: Font size for labels
            title: Optional title for the chart
            padding: Padding between rectangles in pixels
            show_7d: If True, show 7-day performance instead of total P&L
        """
        super().__init__(size, background_color=background_color)
        self.data = data or []
        self.portfolio_fetcher = portfolio_fetcher
        self.text_color = self._convert_color(text_color)
        self.font_size = font_size
        self.title = title
        self.padding = padding
        self.show_7d = show_7d
        self.font_path = os.path.join(RESOURCES_DIR, "fonts/DejaVuSans.ttf")
        # Store percent changes for display
        self.percent_changes: dict = {}

    def update(self, data: Optional[List[Tuple[str, float, str]]] = None):
        """Update the treemap data"""
        if data is not None:
            self.data = data
        elif self.portfolio_fetcher:
            if self.show_7d:
                # Get 7-day performance data: (asset, value_change, percent_change, color)
                perf_data = self.portfolio_fetcher.get_performance_7d_data(refresh=True)
                if perf_data:
                    self.data = [(p[0], p[1], p[3]) for p in perf_data]
                    self.percent_changes = {p[0]: p[2] for p in perf_data}
                else:
                    # Fallback to P&L data if no 7d data available
                    self.data = self.portfolio_fetcher.get_pnl_data(refresh=True)
            else:
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

        # E-ink 7-color palette - EXACT RGB values from display driver
        EINK_GREEN = (0, 255, 0)
        EINK_RED = (255, 0, 0)
        EINK_BLACK = (70, 70, 70)

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
            draw.text((title_x, 5), self.title, fill=EINK_BLACK, font=font)

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

            # Determine color based on P&L sign (e-ink 7-color palette)
            pnl = filtered_data[idx][1]
            fill_color = EINK_GREEN if pnl >= 0 else EINK_RED

            # Draw rectangle
            draw.rectangle(
                [x, y, x + w, y + h],
                fill=fill_color,
                outline='white',
                width=1
            )

            # Draw label if rectangle is big enough
            name = names[idx]
            # Show percentage for 7d mode if available, otherwise show dollar value
            if self.show_7d and name in self.percent_changes:
                pct = self.percent_changes[name]
                value_text = f'{"+" if pct >= 0 else ""}{pct:.1f}%'
            else:
                value_text = f'{"+" if pnl >= 0 else ""}${pnl:,.0f}'

            # Check if text fits
            name_bbox = draw.textbbox((0, 0), name, font=font)
            name_w = name_bbox[2] - name_bbox[0]
            name_h = name_bbox[3] - name_bbox[1]

            pnl_bbox = draw.textbbox((0, 0), value_text, font=small_font)
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
                draw.text((pnl_x, pnl_y), value_text, fill=text_color, font=small_font)

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

        # E-ink black
        EINK_BLACK = (70, 70, 70)
        text = "No P&L data"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2
        draw.text((x, y), text, fill=EINK_BLACK, font=font)

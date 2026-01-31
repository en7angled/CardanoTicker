import logging
from typing import Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from cardano_ticker.data_fetcher.data_fetcher import DataFetcher
from cardano_ticker.widgets.generic.w_abstract import AbstractWidget


class PlotChart(AbstractWidget):
    def __init__(
        self,
        data_fetcher: DataFetcher,
        size: Tuple[int, int],
        symbol: str,
        currency: str,
        increasing_line_color="green",
        decreasing_line_color="red",
        background_color="white",
        text_color="black",
        title=None,
    ):
        """
        Initialize the widget
        Args:
            data_fetcher: The data fetcher object
            symbol: The symbol of the coin
            currency: The currency to compare the coin to
            increasing_line_color: The color of the increasing line
            decreasing_line_color: The color of the decreasing line
            pixel_density: The pixel density of the pixels per unit length
        """

        super().__init__(size, background_color=background_color)
        self.data_fetcher = data_fetcher
        self._symbol = symbol
        self._currency = currency
        self._prices = data_fetcher.get_chart_data(self._symbol, self._currency, 7)
        self._increasing_line_color = increasing_line_color
        self._decreasing_line_color = decreasing_line_color
        text_color = self._convert_color(text_color)
        self.text_color = self._normalize_color(text_color)
        self.title = title

    def __validate_prices(self):
        """
        Validate the prices
        Returns True if valid, False otherwise
        """
        if not isinstance(self._prices, pd.DataFrame):
            prices_type = type(self._prices)
            logging.warning(f"Prices must be a pandas DataFrame, instead got {prices_type}")
            return False

        required_columns = {"open", "close", "high", "low"}
        missing_columns = required_columns - set(self._prices.columns)

        if missing_columns:
            logging.warning(f"Prices DataFrame is missing required columns: {', '.join(missing_columns)}")
            return False

        return True

    @staticmethod
    def __fig2rgb_array(fig):
        fig.canvas.draw()
        buf = fig.canvas.buffer_rgba()
        # convert to a NumPy array
        X = np.asarray(buf)
        return X[:, :, :3]

    def update(self):
        """
        Update the prices
        Args:
            prices: The prices to plot, a pandas dataframe with columns 'open', 'close', 'high', 'low'
        """
        self._prices = self.data_fetcher.get_chart_data(self._symbol, self._currency, 7)

    def render(self):
        # Skip rendering if prices data is invalid
        if self.__validate_prices() is False:
            return

        # create figure
        fig, ax = plt.subplots(figsize=(self.width / 100, self.height / 100))

        # set background color for the chart
        bk_color = np.array(self.background_color) / 255
        ax.set_facecolor(bk_color)
        fig.patch.set_facecolor(bk_color)

        # define width of candlestick elements
        width = 0.6
        width2 = 0.05

        # define up and down prices
        up = self._prices[self._prices.close >= self._prices.open]
        down = self._prices[self._prices.close < self._prices.open]

        # define colors to use
        col1 = self._increasing_line_color  #'#00ff00'
        col2 = self._decreasing_line_color  #'#ff0000'

        # plot up prices
        plt.bar(up.index, up.close - up.open, width, bottom=up.open, color=col1)
        plt.bar(up.index, up.high - up.close, width2, bottom=up.close, color=col1)
        plt.bar(up.index, up.low - up.open, width2, bottom=up.open, color=col1)

        # plot down prices
        plt.bar(down.index, down.close - down.open, width, bottom=down.open, color=col2)
        plt.bar(down.index, down.high - down.open, width2, bottom=down.open, color=col2)
        plt.bar(down.index, down.low - down.close, width2, bottom=down.close, color=col2)

        # rotate x-axis tick labels
        #        t = np.array([self._prices.min().min(), self._prices.max().max()])
        #        plt.yticks(t,t, fontsize=80)
        #        plt.xticks([])

        # 6x10 for 320x320
        font_xy = 6.5 * self.width / 320, 10 * self.height / 320

        # set title
        if self.title is not None:
            plt.title(self.title, fontsize=font_xy[0], color=self.text_color)

        plt.xticks(rotation=0, ha="center", fontsize=font_xy[0], color=self.text_color)
        plt.grid(color=self.text_color, linestyle="--", linewidth=1)
        plt.yticks(rotation=0, ha="right", fontsize=font_xy[1], color=self.text_color)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%d"))

        #   plt.axhline(y = current_price, color = 'r', linewidth=10, linestyle = '--')
        img_arr = self.__fig2rgb_array(fig)
        chart_img = Image.fromarray(img_arr)
        chart_img = chart_img.resize((self.width, self.height))
        # paste the chart image into canvas centered
        self._canvas = chart_img
        plt.close()

from typing import Tuple

import numpy as np
from matplotlib import pyplot as plt
from PIL import Image

from src.widgets.generic.w_abstract import AbstractWidget


class AdaPoolHistWidget(AbstractWidget):
    def __init__(self, data_fetcher, size: Tuple[int, int], pool_id, background_color="white", font_size=25):
        """
        Initialize the widget
        Args:
            data_fetcher: The data fetcher object
            pool_id: The pool id
            pixel_density: The pixel density of the pixels per unit length
        """
        super().__init__(size, background_color=background_color)
        self.data_fetcher = data_fetcher
        self.pool_id = pool_id
        self.pool_data = self.data_fetcher.pool_history(self.pool_id)
        self.font_size = font_size

    def update(self):
        """
        Update the pool history
        """
        self.pool_data = self.data_fetcher.pool_history(self.pool_id)
        self.render()

    def render(self):
        """
        Render the pool history
        pool_data: The pool data to render is a list of dictionaries with keys 'epoch', 'active_stake', 'rewards', 'blocks' obtained with  BlockFrostApi.pool_history
        """

        pool_history = self.pool_data
        # Convert active stake and rewards to integers for easier plotting
        for entry in pool_history:
            entry["active_stake"] = int(entry["active_stake"])
            entry["rewards"] = int(entry["rewards"])

        # Extract data
        epochs = [entry["epoch"] for entry in pool_history]
        active_stake = [entry["active_stake"] / 1e9 for entry in pool_history]  # Convert to billions
        rewards = [entry["rewards"] / 1e6 for entry in pool_history]  # Convert to millions

        # Filter epochs and blocks for red dots
        epochs_with_blocks = [entry["epoch"] for entry in pool_history if entry["blocks"] > 0]
        blocks_with_blocks = [entry["blocks"] for entry in pool_history if entry["blocks"] > 0]

        # Create subplots
        fig, ax1 = plt.subplots()

        fig.set_size_inches(self.width / 100, self.height / 100)

        # Plot active stake
        color = "tab:blue"
        ax1.set_xlabel("Epoch", fontsize=self.font_size)

        # set background color for the chart
        bk_color = np.array(self.background_color) / 255
        ax1.set_facecolor(bk_color)
        fig.patch.set_facecolor(bk_color)

        linewidth = self.width / 500

        ax1.set_ylabel("Active Stake (B ADA)", color=color, fontsize=self.font_size)
        ax1.plot(epochs, active_stake, color=color, label="Active Stake", linewidth=linewidth)
        ax1.tick_params(axis="y", labelcolor=color, labelsize=self.font_size)
        ax1.tick_params(axis="x", labelsize=self.font_size)
        # ax1.legend(loc='upper left')

        # Plot rewards on a secondary y-axis
        ax2 = ax1.twinx()
        color = self._normalize_color(self._convert_color("green"))

        ax2.set_ylabel("Rewards (M ADA)", color=color, fontsize=self.font_size)
        ax2.plot(epochs, rewards, color=color, label="Rewards", linestyle="--", linewidth=linewidth)
        ax2.tick_params(axis="y", labelcolor=color, labelsize=self.font_size)
        # ax2.legend(loc='lower left')

        # Plot blocks as red dots only when blocks > 0
        ax1.scatter(
            epochs_with_blocks,
            blocks_with_blocks,
            color="red",
            label="Blocks Produced (blocks > 0)",
            zorder=5,
        )
        # ax1.legend(loc='lower left')

        # fig.legend(loc='upper right')
        # Add title
        # plt.title("Pool History: Active Stake, Rewards, and Blocks", fontsize=self.font_size)

        # Show plot
        plt.tight_layout()

        # Save the plot as an image
        img_arr = self.__fig2rgb_array(fig)
        chart_img = Image.fromarray(img_arr)
        chart_img = chart_img.resize((self.width, self.height))
        # paste the chart image into canvas centered
        self._canvas = chart_img

        plt.close()

    @staticmethod
    def __fig2rgb_array(fig):
        fig.canvas.draw()
        buf = fig.canvas.buffer_rgba()
        # convert to a NumPy array
        X = np.asarray(buf)
        return X[:, :, :3]

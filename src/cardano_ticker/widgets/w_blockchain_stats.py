import os

from PIL import ImageFont

from cardano_ticker.utils.constants import RESOURCES_DIR
from cardano_ticker.utils.currency import PriceCurrency
from cardano_ticker.widgets.generic.w_charts_generic import (
    LineChartWidget,
    ProgressBarWidget,
)
from cardano_ticker.widgets.generic.w_table_generic import TableWidget


class BlockchainTransactionsWidget(LineChartWidget):
    def __init__(
        self,
        data_fetcher,
        size,
        background_color="white",
        font_size=22,
        line_color="blue",
    ):
        self.data_fetcher = data_fetcher
        self.line_color = line_color
        super().__init__(
            size,
            [],
            [],
            background_color=background_color,
            font_size=font_size,
            title="Transactions past 30 minutes",
        )

    def update(self):
        blockchain_stats = self.data_fetcher.blockchain_stats()
        l_data = [("tx nb", blockchain_stats["transactions"]["transactions"])]
        super().update(l_data, [self.line_color])


class BlockchainProgressWidget(ProgressBarWidget):
    def __init__(self, data_fetcher, size, background_color=(0.3, 0.3, 0.3), font_size=20):
        self.data_fetcher = data_fetcher
        super().__init__(size, 0, background_color=background_color, font_size=font_size)

    def update(self):
        blockchain_stats = self.data_fetcher.blockchain_stats()
        super().update(blockchain_stats["percentage_progress"])


class BlockchainStatsTable(TableWidget):
    def __init__(
        self,
        data_fetcher,
        size,
        background_color="gray",
        header_orientation="columns",
        font_size=20,
        text_color="blue",
        header_color="black",
    ):
        self.data_fetcher = data_fetcher
        f_file = os.path.join(RESOURCES_DIR, "fonts/DejaVuSans.ttf")
        font = ImageFont.truetype(f_file, font_size)
        super().__init__(
            size,
            [],
            [],
            font,
            header_orientation=header_orientation,
            header_color=header_color,
            row_color=text_color,
            background_color=background_color,
        )

    def update(self):
        blockchain_stats = self.data_fetcher.blockchain_stats()
        headers = ["Epoch", "Active Stake", "Total Stake Pools", "Remaining Time"]

        active_stake = blockchain_stats["active_stake"]
        rows = [
            [
                str(blockchain_stats["epoch_number"]),
                f"{active_stake}b {PriceCurrency.ADA.get_symbol()}",
                str(blockchain_stats["total_stake_pools"]),
                blockchain_stats["remaining_time"],
            ]
        ]

        super().update(headers, rows, self.header_orientation)

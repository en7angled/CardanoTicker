import os

from PIL import ImageFont

from src.utils.constants import RESOURCES_DIR
from src.utils.currency import PriceCurrency
from src.widgets.generic.w_charts_generic import BarChartWidget, PieChartWidget
from src.widgets.generic.w_table_generic import TableWidget


class PoolInfoTable(TableWidget):
    def __init__(
        self,
        size,
        datafetcher,
        pool_id,
        background_color="gray",
        header_orientation="columns",
        font_size=10,
        header_color="black",
        text_color="blue",
    ):
        self.datafetcher = datafetcher
        self.pool_id = pool_id
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
        data = self.datafetcher.pool(self.pool_id)
        headers = [
            "Live",
            "Active",
            "Saturation",
            "Delegators",
            "Blocks Minted",
            "Live Pledege",
            "Declared Pledge",
        ]
        rows = [
            [
                f"{int(int(data['live_stake']) / 1e6)} {PriceCurrency.ADA.get_symbol()}",
                f"{int(int(data['active_stake']) / 1e6)} {PriceCurrency.ADA.get_symbol()}",
                f"{round(data['live_saturation'],4)}%",
                f"{data['live_delegators']}",
                f"{data['blocks_minted']}",
                f"{int(int(data['live_pledge']) / 1e6)} {PriceCurrency.ADA.get_symbol()}",
                f"{int(int(data['declared_pledge']) / 1e6)} {PriceCurrency.ADA.get_symbol()}",
            ]
        ]

        super().update(headers, rows, self.header_orientation)


class PoolStakeBarChart(BarChartWidget):
    def __init__(
        self,
        size,
        datafetcher,
        pool_id,
        background_color=(0.7, 0.7, 0.7, 0.5),
        font_size=22,
    ):
        self.datafetcher = datafetcher
        self.pool_id = pool_id
        super().__init__(size, [], [], background_color=background_color, font_size=font_size)

    def update(self):
        data = self.datafetcher.pool(self.pool_id)
        chart_data = [
            ("Live Stake", int(data["live_stake"]) // 1e6),
            ("Active Stake", int(data["active_stake"]) // 1e6),
            ("Live Pledge", int(data["live_pledge"]) // 1e6),
        ]
        pie_chart_colors = ["blue", "green", "purple"]
        super().update(chart_data, pie_chart_colors)


class SupplyPieChartWidget(PieChartWidget):
    def __init__(self, data_fetcher, size, background_color=(0.3, 0.3, 0.3), font_size=20):
        super().__init__(size, [], [], background_color, font_size=font_size)
        self.data_fetcher = data_fetcher

    def update(self):
        data = self.data_fetcher.network()
        # Create bar widget for supply
        chart_data = [
            ("Circulating", int(data["supply"]["circulating"])),
            ("Locked", int(data["supply"]["locked"])),
            ("Treasury", int(data["supply"]["treasury"])),
            ("Reserves", int(data["supply"]["reserves"])),
        ]
        bar_chart_colors = ["green", "blue", "purple", "orange"]
        super().update(chart_data, bar_chart_colors)

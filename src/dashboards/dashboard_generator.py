from src.utils.currency import currency_from_str
from src.widgets.generic.w_text import DateTimeWidget, GenericTextWidget, MutiTextWidget
from src.widgets.w_blockchain_stats import (
    BlockchainProgressWidget,
    BlockchainStatsTable,
    BlockchainTransactionsWidget,
)
from src.widgets.w_coin_price import (
    AdaPriceWithLogo,
    BtcPriceWithLogo,
    EthPriceWithLogo,
)
from src.widgets.w_layout import WidgetLayout
from src.widgets.w_plot_chart import PlotChart
from src.widgets.w_pool import PoolInfoTable, PoolStakeBarChart, SupplyPieChartWidget
from src.widgets.w_pool_history import AdaPoolHistWidget


class DashboardGenerator:
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher

    def json_to_layout(self, data: dict) -> WidgetLayout:
        """
        Convert json data to layout
        """
        data_fetcher = self.data_fetcher
        canvas_size = data["canvas_size"]
        background_color = data["background_color"] if "background_color" in data else "white"
        layout = WidgetLayout(canvas_size, background_color=background_color)

        for widget_data in data["dashboard"]:
            widget_type = widget_data["type"]
            position = widget_data["position"]
            position = (
                int(position[0] * canvas_size[0]),
                int(position[1] * canvas_size[1]),
            )

            size = widget_data["size"]
            size = (int(size[0] * canvas_size[0]), int(size[1] * canvas_size[1]))
            text_color = widget_data["text_color"] if "text_color" in widget_data else "black"
            background_color = widget_data["background_color"] if "background_color" in widget_data else "white"

            if "data" in widget_data:
                font_size = widget_data["data"]["font_size"] if "font_size" in widget_data["data"] else 10

            widget = None
            if widget_type == "ada_price":
                currencies = [currency_from_str(c) for c in widget_data["data"]["currency"]]
                widget = AdaPriceWithLogo(
                    data_fetcher,
                    size,
                    currency=currencies,
                    background_color=background_color,
                    text_color=text_color,
                )
            elif widget_type == "btc_price":
                currencies = [currency_from_str(c) for c in widget_data["data"]["currency"]]
                widget = BtcPriceWithLogo(
                    data_fetcher,
                    size,
                    currency=currencies,
                    background_color=background_color,
                    text_color=text_color,
                )
            elif widget_type == "eth_price":
                currencies = [currency_from_str(c) for c in widget_data["data"]["currency"]]
                widget = EthPriceWithLogo(
                    data_fetcher,
                    size,
                    currency=currencies,
                    background_color=background_color,
                    text_color=text_color,
                )
            elif widget_type == "plot_chart":
                inc_col = widget_data["increasing_line_color"] if "increasing_line_color" in widget_data else "green"
                dec_col = widget_data["decreasing_line_color"] if "decreasing_line_color" in widget_data else "red"

                widget = PlotChart(
                    data_fetcher,
                    size,
                    symbol=widget_data["data"]["symbol"],
                    currency=widget_data["data"]["currency"],
                    background_color=background_color,
                    increasing_line_color=inc_col,
                    decreasing_line_color=dec_col,
                )
            elif widget_type == "date_text":
                widget = DateTimeWidget(size, text_color=text_color, background_color=background_color)
            elif widget_type == "pool_info_table":
                widget = PoolInfoTable(
                    size,
                    data_fetcher,
                    widget_data["data"]["pool_id"],
                    font_size=font_size,
                    header_orientation=widget_data["data"]["header_orientation"],
                    background_color=background_color,
                )
            elif widget_type == "pool_stake_bar_chart":
                widget = PoolStakeBarChart(
                    size,
                    data_fetcher,
                    widget_data["data"]["pool_id"],
                    font_size=font_size,
                    background_color=background_color,
                )
            elif widget_type == "pool_history_chart":
                widget = AdaPoolHistWidget(
                    data_fetcher,
                    size,
                    widget_data["data"]["pool_id"],
                    background_color=background_color,
                    font_size=font_size,
                )
            elif widget_type == "supply_pie_chart":
                widget = SupplyPieChartWidget(
                    data_fetcher,
                    size,
                    font_size=font_size,
                    background_color=background_color,
                )
            elif widget_type == "text":
                auto_aj = False if "auto_adjust_font" in widget_data["data"] else True
                widget = GenericTextWidget(
                    widget_data["data"]["text"],
                    size,
                    text_color=text_color,
                    background_color=background_color,
                    auto_adjust_font=auto_aj,
                )
            elif widget_type == "multi_text":
                widget = MutiTextWidget(
                    size,
                    widget_data["data"]["texts"],
                    text_color=text_color,
                    background_color=background_color,
                )
            elif widget_type == "blockchain_progress":
                widget = BlockchainProgressWidget(
                    data_fetcher,
                    size,
                    background_color=background_color,
                    font_size=font_size,
                )
            elif widget_type == "blockchain_stats_table":
                header_color = widget_data["data"]["header_color"] if "header_color" in widget_data["data"] else "black"
                widget = BlockchainStatsTable(
                    data_fetcher,
                    size,
                    background_color=background_color,
                    font_size=font_size,
                    header_orientation=widget_data["data"]["header_orientation"],
                    header_color=header_color,
                )
            elif widget_type == "blockchain_transactions":
                widget = BlockchainTransactionsWidget(
                    data_fetcher,
                    size,
                    background_color=background_color,
                    font_size=font_size,
                    line_color=widget_data["data"]["line_color"],
                )
            else:
                raise ValueError(f"Widget type {widget_type} not found")

            layout.add_widget(widget, position)
        return layout

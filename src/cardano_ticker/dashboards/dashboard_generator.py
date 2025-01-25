from cardano_ticker.utils.currency import currency_from_str
from cardano_ticker.widgets.generic.w_text import (
    DateTimeWidget,
    GenericTextWidget,
    MutiTextWidget,
)
from cardano_ticker.widgets.w_blockchain_stats import (
    BlockchainProgressWidget,
    BlockchainStatsTable,
    BlockchainTransactionsWidget,
)
from cardano_ticker.widgets.w_coin_price import (
    AdaPriceWithLogo,
    BtcPriceWithLogo,
    EthPriceWithLogo,
)
from cardano_ticker.widgets.w_layout import WidgetLayout
from cardano_ticker.widgets.w_plot_chart import PlotChart
from cardano_ticker.widgets.w_pool import (
    PoolInfoTable,
    PoolStakeBarChart,
    SupplyPieChartWidget,
)
from cardano_ticker.widgets.w_pool_history import AdaPoolHistWidget


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

    @staticmethod
    def __replace_placeholders_in_json(json_data, placeholders_name, value):
        """
        Replace placeholders in a json with the value
        """

        # if a field in json is a string of the form @placeholder_name, replace it with the value
        if isinstance(json_data, dict):
            for k, v in json_data.items():
                json_data[k] = DashboardGenerator.__replace_placeholders_in_json(v, placeholders_name, value)
        elif isinstance(json_data, list):
            for i, v in enumerate(json_data):
                json_data[i] = DashboardGenerator.__replace_placeholders_in_json(v, placeholders_name, value)
        elif isinstance(json_data, str):
            if json_data == f"@{placeholders_name}":
                return value

        return json_data

    @staticmethod
    def update_dashboard_description(dashboard_description, values_dict):
        """
        Update the dashboard description with values from the configuration
        The values_dict is a dictionary with the placeholder name as key and the value as value
        Returns the updated dashboard description
        """
        # update the dashboard description with the configuration
        for k, v in values_dict.items():
            dashboard_description = DashboardGenerator.__replace_placeholders_in_json(dashboard_description, k, v)

        return dashboard_description

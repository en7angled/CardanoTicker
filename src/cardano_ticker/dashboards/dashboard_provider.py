import json
import os
import sys
import time

from PIL import Image

from cardano_ticker.dashboards.dashboard_generator import DashboardGenerator
from cardano_ticker.data_fetcher.data_fetcher import DataFetcher
from cardano_ticker.utils.constants import RESOURCES_DIR

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))


def main():

    # read configuration
    default_config_path = os.path.join(RESOURCES_DIR, "config.json")
    ticker_config_path = os.environ.get("TICKER_CONFIG_PATH", default_config_path)
    config = json.load(open(ticker_config_path, "r"))

    # read configuration values
    refresh_interval_s = config.get("refresh_interval", 60)
    output_dir = config.get("output_dir", RESOURCES_DIR)
    if output_dir is None:
        output_dir = RESOURCES_DIR

    SAMPLES_DIR = os.path.join(RESOURCES_DIR, "dashboard_samples")
    dashboard_dir = config.get("dashboard_path", SAMPLES_DIR)
    if dashboard_dir is None:
        dashboard_dir = SAMPLES_DIR

    dashboard_name = config.get("dashboard_name", "price_dashboard_example")

    # create fetcher and generator
    fetcher = DataFetcher(blockfrost_project_id=config["blockfrost_project_id"])
    generator = DashboardGenerator(fetcher)

    # get pool name and ticker
    name, ticker = fetcher.pool_name_and_ticker(config["pool_id"])
    value_dict = {
        "pool_name": f" [{ticker}] {name} ",
        "pool_id": config["pool_id"],
    }

    filename = f"{dashboard_name}.json"
    dashboard_description_file = os.path.join(dashboard_dir, filename)
    dashboard_description = json.load(open(dashboard_description_file, "r"))

    # update dashboard description with configuration values
    dashboard_description = DashboardGenerator.update_dashboard_description(dashboard_description, value_dict)

    # create dashboard
    dashboard = generator.json_to_layout(dashboard_description)

    while True:
        dashboard_img = dashboard.render()

        # save output on disk
        out = dashboard_img.transpose(Image.ROTATE_180)
        out.save(os.path.join(output_dir, "frame.bmp"))
        print(output_dir, "SAVED!")

        time.sleep(refresh_interval_s)

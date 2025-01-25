import json
import os
import sys
import time

from dashboards.dashboard_generator import DashboardGenerator
from data_fetcher import DataFetcher
from PIL import Image

from cardano_ticker.utils.constants import RESOURCES_DIR

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "samples")


while True:

    # read configuration
    config_file = os.path.join(RESOURCES_DIR, "config.json")
    config = json.load(open(config_file, "r"))

    fetcher = DataFetcher(blockfrost_project_id=config["blockfrost_project_id"])
    generator = DashboardGenerator(fetcher)

    name, ticker = fetcher.pool_name_and_ticker(config["pool_id"])
    value_dict = {
        "pool_name": f" [{ticker}] {name} ",
        "pool_id": config["pool_id"],
    }

    dashboard_dir = config.get("dashboard_path", SAMPLES_DIR)
    dashboard_name = config.get("dashboard_name", "price_dashboard_example")
    dashboard_description_file = os.path.join(dashboard_dir, f"{dashboard_name}.json")

    dashboard_description = json.load(open(dashboard_description_file, "r"))

    # update dashboard description with configuration values
    dashboard_description = DashboardGenerator.update_dashboard_description(dashboard_description, value_dict)

    # create dashboard
    dashboard = generator.json_to_layout(dashboard_description)
    dashboard_img = dashboard.render()

    # save output on disk
    out = dashboard_img.transpose(Image.ROTATE_180)
    out.save(os.path.join(RESOURCES_DIR, "frame.bmp"))
    print(RESOURCES_DIR, "SAVED!")

    time.sleep(1500)

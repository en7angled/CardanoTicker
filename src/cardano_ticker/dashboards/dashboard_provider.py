import json
import os
import sys
import time

from dashboards.dashboard_generator import DashboardGenerator
from data_fetcher import DataFetcher
from PIL import Image

from cardano_ticker.utils.constants import RESOURCES_DIR

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))

dashboard_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "dashboards")


fetcher = DataFetcher()
generator = DashboardGenerator(fetcher)

IMG_HW = (400, 640)

dashboard_description_file = os.path.join(dashboard_dir, "price_dashboard_example.json")

while True:

    # get dashboard description
    with open(dashboard_description_file, "r") as f:
        dashboard_description = json.load(f)

        # create dashboard
        dashboard = generator.json_to_layout(dashboard_description)
        dashboard_img = dashboard.render()

        # save output on disk
        out = dashboard_img.transpose(Image.ROTATE_180)
        out.save(os.path.join(RESOURCES_DIR, "frame.bmp"))
        print(RESOURCES_DIR, "SAVED!")

    time.sleep(1500)

import json
import logging
import os
import sys
import time

from PIL import Image

from cardano_ticker.dashboards.dashboard_generator import DashboardGenerator
from cardano_ticker.data_fetcher.data_fetcher import DataFetcher
from cardano_ticker.utils.constants import RESOURCES_DIR

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))

# Initialize logging
logging.basicConfig(level=logging.DEBUG)


def read_config():
    """
    Read configuration file, and return the configuration dictionary
    """

    # read configuration
    default_config_path = os.path.join(RESOURCES_DIR, "config.json")
    ticker_config_path = os.environ.get("TICKER_CONFIG_PATH", default_config_path)

    try:
        config = json.load(open(ticker_config_path, "r"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file {ticker_config_path} not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Config file {ticker_config_path} is not a valid json file.")
    except Exception as e:
        raise ValueError(f"Error reading config file {ticker_config_path}: {e}")
    return config


def create_dashboard(data_fetcher, dashboard_generator, config):
    """
    Create the dashboard from the configuration, and return it
    """

    SAMPLES_DIR = os.path.join(RESOURCES_DIR, "dashboard_samples")
    dashboard_dir = config.get("dashboard_path", SAMPLES_DIR)
    if dashboard_dir is None:
        dashboard_dir = SAMPLES_DIR

    dashboard_name = config.get("dashboard_name", "price_dashboard_example")

    # get pool name and ticker
    name, ticker = data_fetcher.pool_name_and_ticker(config["pool_id"])
    value_dict = {
        "pool_name": f" [{ticker}] {name} ",
        "pool_id": config["pool_id"],
    }

    filename = f"{dashboard_name}.json"
    dashboard_description_file = os.path.join(dashboard_dir, filename)

    try:
        dashboard_description = json.load(open(dashboard_description_file, "r"))
    except FileNotFoundError:
        raise FileNotFoundError(f"Dashboard file {dashboard_description_file} not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Dashboard file {dashboard_description_file} is not a valid json file.")
    except Exception as e:
        raise ValueError(f"Error reading dashboard file {dashboard_description_file}: {e}")

    # update dashboard description with configuration values
    dashboard_description = DashboardGenerator.update_dashboard_description(dashboard_description, value_dict)

    # create dashboard
    try:
        dashboard = dashboard_generator.json_to_layout(dashboard_description)
    except Exception as e:
        raise ValueError(f"Error creating dashboard: {e}")

    return dashboard


def main():
    """
    Main function, that reads the configuration, creates the dashboard, and updates it at regular intervals
    """

    # read configuration
    config = read_config()
    logging.info(f"Configuration: {config}")

    # extract configuration values
    refresh_interval_s = config.get("refresh_interval_s", 60)
    output_dir = config.get("output_dir", RESOURCES_DIR)
    if output_dir is None:
        output_dir = RESOURCES_DIR

    logging.info(f"Output directory: {output_dir}")

    # create fetcher and generator
    fetcher = DataFetcher(blockfrost_project_id=config["blockfrost_project_id"])
    generator = DashboardGenerator(fetcher)

    # create dashboard
    logging.info("Creating dashboard")
    dashboard = create_dashboard(fetcher, generator, config)
    logging.info("Dashboard created")

    while True:
        # update dashboard
        dashboard_img = dashboard.render()

        # save output on disk
        out = dashboard_img.transpose(Image.ROTATE_180)
        out.save(os.path.join(output_dir, "frame.bmp"))
        logging.info(f"{output_dir} SAVED!")

        # wait for the next refresh
        time.sleep(refresh_interval_s)


if __name__ == "__main__":
    main()

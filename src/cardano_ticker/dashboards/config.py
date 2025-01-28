import os
import json
from cardano_ticker.utils.constants import RESOURCES_DIR

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
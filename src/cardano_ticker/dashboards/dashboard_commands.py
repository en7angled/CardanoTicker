from enum import Enum

class DashboardCommand(Enum):
    """
    Enum to represent the commands that can be sent to the dashboard manager
    """
    LOAD_DASHBOARD = "load_dashboard"
    GET_LAST_IMAGE = "get_last_image"
    GET_IMAGE_HASH = "get_image_hash"
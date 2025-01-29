import hashlib
import json
import logging
import os
import socket
import struct
import sys
import threading
import time

from cardano_ticker.dashboards.config import read_config
from cardano_ticker.dashboards.dashboard_commands import (
    DashboardCommand,
    DashboardResponses,
)
from cardano_ticker.dashboards.dashboard_generator import DashboardGenerator
from cardano_ticker.data_fetcher.data_fetcher import DataFetcher
from cardano_ticker.utils.constants import RESOURCES_DIR

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__))))

# Initialize logging
logging.basicConfig(level=logging.INFO)


class DashboardManager:
    """
    Class to manage the rendering of the dashboard, and the socket server
    """

    def __init__(self) -> None:

        # read configuration
        self.config = read_config()
        logging.info(f"Configuration: {self.config}")

        # extract configuration values
        self.refresh_interval_s = self.config.get("refresh_interval_s", 60)
        self.output_dir = self.config.get("output_dir", RESOURCES_DIR)
        if self.output_dir is None:
            self.output_dir = RESOURCES_DIR
        logging.info(f"Output directory: {self.output_dir}")

        SAMPLES_DIR = os.path.join(RESOURCES_DIR, "dashboard_samples")
        dashboard_dir = self.config.get("dashboard_path", SAMPLES_DIR)
        if dashboard_dir is None:
            dashboard_dir = SAMPLES_DIR
        self.dashboard_dir = dashboard_dir
        logging.info(f"Dashboard directory: {self.dashboard_dir}")

        # create fetcher and generator
        self.fetcher = DataFetcher(blockfrost_project_id=self.config["blockfrost_project_id"])
        self.dashboard_generator = DashboardGenerator(self.fetcher)
        self.current_dashboard = None
        self.mutex = threading.Lock()
        self.last_image = None

    def __get_dashboard_file_from_config(self):
        """
        Get the dashboard file from the configuration
        """

        dashboard_name = self.config.get("dashboard_name", "price_dashboard_example")
        filename = f"{dashboard_name}.json"
        dashboard_description_file = os.path.join(self.dashboard_dir, filename)
        return dashboard_description_file

    def create_dashboard(self, dashboard_description_file):
        """
        Create the dashboard from the configuration, and return it
        """
        # create dashboard
        logging.info("Creating dashboard")

        # get pool name and ticker
        name, ticker = self.fetcher.pool_name_and_ticker(self.config["pool_id"])
        value_dict = {
            "pool_name": f" [{ticker}] {name} ",
            "pool_id": self.config["pool_id"],
        }

        try:
            dashboard_description = json.load(open(dashboard_description_file, "r"))
        except FileNotFoundError:
            logging.error(f"Dashboard file {dashboard_description_file} not found.")
            return None
        except json.JSONDecodeError:
            logging.error(f"Dashboard file {dashboard_description_file} is not a valid json file.")
            return None
        except Exception as e:
            logging.error(f"Error reading dashboard file {dashboard_description_file}: {e}")
            return None

        # update dashboard description with configuration values
        dashboard_description = DashboardGenerator.update_dashboard_description(dashboard_description, value_dict)

        # create dashboard
        try:
            dashboard = self.dashboard_generator.json_to_layout(dashboard_description)
        except Exception as e:
            logging.error(f"Error creating dashboard: {e}")
            return None

        logging.info("Dashboard created")
        return dashboard

    def update_frame(self):
        # update dashboard
        self.mutex.acquire()
        out = self.current_dashboard.render()
        self.last_image = out
        self.last_image_hash = hashlib.md5(out.tobytes()).hexdigest()
        self.last_update_time = time.time()
        self.mutex.release()

    def render_loop(self):

        dashboard_file = self.__get_dashboard_file_from_config()

        self.mutex.acquire()
        self.current_dashboard = self.create_dashboard(dashboard_file)
        self.mutex.release()
        if self.current_dashboard is None:
            raise ValueError("Dashboard could not be created")

        self.update_frame()

        while True:
            now = time.time()
            if now > self.last_update_time + self.refresh_interval_s:
                logging.info("Updating frame")
                self.update_frame()
                # save output on disk
                out = self.last_image  # .transpose(Image.ROTATE_180)
                out.save(os.path.join(self.output_dir, "frame.bmp"))
                logging.info(f"Frame saved at: {self.output_dir} !")

            # wait for the next refresh
            time.sleep(1)

    def start_socket_server(self, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", port))
        self.server.listen(5)
        logging.info(f"Socket server started on port {port}")

        while True:
            client_socket, addr = self.server.accept()
            logging.info(f"Accepted connection from {addr}")
            client_handler = threading.Thread(
                target=DashboardManager.handle_client_connection, args=(self, client_socket)
            )
            client_handler.start()

    def stop_socket_server(self):
        self.server.close()

    def handle_client_connection(self, client_socket):
        while True:
            # read the request
            request = client_socket.recv(1024).decode()
            if not request:
                break

            command, *args = request.split()
            logging.info(type(command))
            logging.info(f"Received command: {command}")
            if command == DashboardCommand.LOAD_DASHBOARD.value:
                if len(args) != 1:
                    response = DashboardResponses.INVALID_ARGUMENTS.value
                    client_socket.send(response.encode())
                    continue
                dashboard_name = args[0]
                dashboard_file = os.path.join(self.dashboard_dir, f"{dashboard_name}.json")
                dashboard = self.create_dashboard(dashboard_file)
                if dashboard is None:
                    logging.error("Error creating dashboard")
                    client_socket.send(DashboardResponses.ERROR_CREATING_DASHBOARD.value.encode())
                else:
                    # make sure to update the current dashboard in a thread-safe manner
                    self.mutex.acquire()
                    self.current_dashboard = dashboard
                    # force an update of the frame
                    self.last_update_time = time.time() - self.refresh_interval_s
                    self.mutex.release()
                    client_socket.send(DashboardResponses.DASHBOARD_LOADED.value.encode())
            elif command == DashboardCommand.GET_LAST_IMAGE.value:
                if self.last_image is None:
                    client_socket.sendall(struct.pack('!II', 0, 0))
                    continue

                resp_data = DashboardResponses.get_image_response(self.last_image)
                for resp in resp_data:
                    client_socket.sendall(resp)
            elif command == DashboardCommand.GET_IMAGE_HASH.value:
                resp = DashboardResponses.get_image_hash_response(self.last_image_hash)
                client_socket.send(resp)
            else:
                client_socket.send(DashboardResponses.UNKNOWN_COMMAND.value.encode())

        client_socket.close()


def main():
    """
    Main function, to start the rendering loop and the socket server
    """

    dashboard_manager = DashboardManager()

    # start the socket server
    port = dashboard_manager.config.get("socket_port", 9999)
    socket_thread = threading.Thread(target=dashboard_manager.start_socket_server, args=(port,))
    socket_thread.start()

    # start the rendering loop, matplotlib outside of the main thread will cause issues
    # so render loop is started on main thread
    try:
        dashboard_manager.render_loop()
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, stopping server")
        dashboard_manager.stop_socket_server()

    dashboard_manager.stop_socket_server()


if __name__ == "__main__":
    main()

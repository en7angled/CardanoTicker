import hashlib
import json
import logging
import os
import socket
import struct
import sys
import threading
import time

from flask import Flask, send_file

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
    Class to manage the rendering of the dashboard, socket server, and HTTP server.
    """

    def __init__(self):
        # Read configuration
        self.config = read_config()
        logging.info(f"Configuration: {self.config}")

        # Extract configuration values
        self.refresh_interval_s = self.config.get("refresh_interval_s", 60)
        self.output_dir = self.config.get("output_dir", RESOURCES_DIR) or RESOURCES_DIR
        logging.info(f"Output directory: {self.output_dir}")

        SAMPLES_DIR = os.path.join(RESOURCES_DIR, "dashboard_samples")
        self.dashboard_dir = self.config.get("dashboard_path", SAMPLES_DIR) or SAMPLES_DIR
        logging.info(f"Dashboard directory: {self.dashboard_dir}")

        # Create data fetcher and dashboard generator
        self.fetcher = DataFetcher(blockfrost_project_id=self.config["blockfrost_project_id"])
        self.dashboard_generator = DashboardGenerator(self.fetcher)
        self.current_dashboard = None
        self.mutex = threading.Lock()
        self.last_image = None
        self.last_image_hash = None
        self.last_update_time = None

        # Create Flask app for HTTP server
        self.app = Flask(__name__)

        @self.app.route('/latest-image')
        def get_latest_image():
            """
            HTTP Endpoint to serve the latest color dashboard image.
            """
            image_path = os.path.join(self.output_dir, "frame.bmp")
            if not os.path.exists(image_path):
                return "No image available", 404
            return send_file(image_path, mimetype='image/bmp')

        @self.app.route('/latest-image-bw')
        def get_latest_image_bw():
            """
            HTTP Endpoint to serve the black-and-white dashboard image.
            """
            bw_image_path = os.path.join(self.output_dir, "frame_bw.bmp")
            if not os.path.exists(bw_image_path):
                return "No black-and-white image available", 404
            return send_file(bw_image_path, mimetype='image/bmp')

    def __get_dashboard_file_from_config(self):
        """
        Get the dashboard file from the configuration.
        """
        dashboard_name = self.config.get("dashboard_name", "price_dashboard_example")
        return os.path.join(self.dashboard_dir, f"{dashboard_name}.json")

    def create_dashboard(self, dashboard_description_file):
        """
        Create the dashboard from the configuration and return it.
        """
        logging.info("Creating dashboard")

        # Get pool name and ticker
        name, ticker = self.fetcher.pool_name_and_ticker(self.config["pool_id"])
        value_dict = {"pool_name": f" [{ticker}] {name} ", "pool_id": self.config["pool_id"]}

        try:
            with open(dashboard_description_file, "r") as file:
                dashboard_description = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error reading dashboard file {dashboard_description_file}: {e}")
            return None

        # Update dashboard description with configuration values
        dashboard_description = DashboardGenerator.update_dashboard_description(dashboard_description, value_dict)

        try:
            dashboard = self.dashboard_generator.json_to_layout(dashboard_description)
        except Exception as e:
            logging.error(f"Error creating dashboard: {e}")
            return None

        logging.info("Dashboard created successfully.")
        return dashboard

    def update_frame(self):
        """
        Render the dashboard and save it as an image (both color and black-and-white).
        """
        with self.mutex:
            out = self.current_dashboard.render()
            self.last_image = out
            self.last_image_hash = hashlib.md5(out.tobytes()).hexdigest()
            self.last_update_time = time.time()

        # Save full-color image
        color_image_path = os.path.join(self.output_dir, "frame.bmp")
        out.save(color_image_path)
        logging.info(f"Dashboard image saved at: {color_image_path}")

        # Convert to black-and-white (1-bit) and save it
        bw_image_path = os.path.join(self.output_dir, "frame_bw.bmp")
        bw_image = out.convert("1")  # Convert to 1-bit black & white
        # save the image as 1-bit bitmap
        bw_image.save(bw_image_path)

        logging.info(f"Black & white dashboard image saved at: {bw_image_path}")

    def render_loop(self):
        """
        Main loop to periodically update the dashboard image.
        """
        dashboard_file = self.__get_dashboard_file_from_config()

        with self.mutex:
            self.current_dashboard = self.create_dashboard(dashboard_file)

        if self.current_dashboard is None:
            raise ValueError("Dashboard could not be created.")

        self.update_frame()

        while True:
            now = time.time()
            if now > self.last_update_time + self.refresh_interval_s:
                logging.info("Updating dashboard frame...")
                self.update_frame()
            time.sleep(1)  # Avoid CPU overuse

    def start_http_server(self, port=5000):
        """
        Start Flask HTTP server for serving the latest image.
        """
        logging.info(f"Starting HTTP server on port {port}")
        self.app.run(host="0.0.0.0", port=port, threaded=True)

    def start_socket_server(self, port=9999):
        """
        Start socket server for handling client commands.
        """
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", port))
        self.server.listen(5)
        logging.info(f"Socket server started on port {port}")

        while True:
            client_socket, addr = self.server.accept()
            logging.info(f"Accepted connection from {addr}")
            client_handler = threading.Thread(target=self.handle_client_connection, args=(client_socket,))
            client_handler.start()

    def handle_client_connection(self, client_socket):
        """
        Handle incoming socket client commands.
        """
        while True:
            request = client_socket.recv(1024).decode()
            if not request:
                break

            command, *args = request.split()
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

    def start_servers(self):
        """
        Start both Flask HTTP and socket servers in separate threads.
        """
        socket_port = self.config.get("socket_port", 9999)
        flask_port = self.config.get("flask_port", 5000)

        flask_thread = threading.Thread(target=self.start_http_server, args=(flask_port,), daemon=True)
        flask_thread.start()

        socket_thread = threading.Thread(target=self.start_socket_server, args=(socket_port,))
        socket_thread.start()

        # Run rendering loop in the main thread
        self.render_loop()


def main():
    """
    Main function to start the dashboard manager.
    """
    dashboard_manager = DashboardManager()
    dashboard_manager.start_servers()


if __name__ == "__main__":
    main()

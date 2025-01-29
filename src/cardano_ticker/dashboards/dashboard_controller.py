import cmd
import logging
import socket
import struct

from PIL import Image

from cardano_ticker.dashboards.config import read_config
from cardano_ticker.dashboards.dashboard_commands import DashboardCommand


# create a dashboard controller client that can send commands to the dashboard manager
class DashboardController:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def send_command(self, command: DashboardCommand, args: list = []):
        """
        Send a command to the dashboard manager
        """
        logging.info(f"Sending command: {command.value} with args: {args}")
        request = f"{command.value} {' '.join(args)}"
        self.socket.sendall(str(request).encode())

    def change_dashboard(self, dashboard_name: str):
        """
        Change the dashboard to the specified dashboard name
        """
        self.send_command(DashboardCommand.LOAD_DASHBOARD, [dashboard_name])
        response = self.socket.recv(1024).decode().strip()
        logging.info(f"Received response: {response}")

    def get_last_image(self):
        """
        Get the last image from the dashboard manager
        """
        self.send_command(DashboardCommand.GET_LAST_IMAGE)
        return self.receive_image()

    def get_last_image_hash(self):
        """
        Get the hash of the last image from the dashboard manager
        """
        self.send_command(DashboardCommand.GET_IMAGE_HASH)
        return self.socket.recv(1024).decode().strip()

    def receive_image(self):

        # receive the width and height of the image
        width, height = struct.unpack('!II', self.socket.recv(8))
        if width == 0 or height == 0:
            return None
        logging.info(f"Received image with width: {width} and height: {height}")
        # receive the size of the image
        img_size = struct.unpack('!I', self.socket.recv(4))[0]
        logging.info(f"Received image with size: {img_size}")
        # receive the image data
        img_data = b''
        while len(img_data) < img_size:
            packet = self.socket.recv(1024)
            logging.info(f"Received packet of size: {len(packet)}")
            if not packet:
                break
            img_data += packet
        # create an image from the received data
        img = Image.frombytes('RGB', (width, height), img_data)
        return img

    def close(self):
        self.socket.close()


class DashboardControllerCLI(cmd.Cmd):
    intro = 'Welcome to the Dashboard Controller CLI. Type help or ? to list commands.\n'
    prompt = '(dashboard) '

    def __init__(self, host, port):
        super().__init__()
        self.controller = DashboardController(host, port)

    def do_get_last_image(self, arg):
        'Get the last image from the dashboard manager and display it.'
        img = self.controller.get_last_image()
        if img:
            img.show()
        else:
            print("No image received.")

    def do_get_last_image_hash(self, arg):
        'Get the hash of the last image from the dashboard manager.'
        img_hash = self.controller.get_last_image_hash()
        print(f"Image hash: {img_hash}")

    def do_change_dashboard(self, arg):
        'Change the dashboard to the specified dashboard name.'
        print(f"Changed dashboard to {arg}")
        self.controller.change_dashboard(arg)

    def do_exit(self, arg):
        'Exit the CLI.'
        print('Exiting...')
        self.controller.close()
        return True


def controller():
    """
    Main function to start the dashboard controller client
    """
    logging.basicConfig(level=logging.INFO)
    config = read_config()
    port = config.get("socket_port", 9999)

    logging.info("Starting dashboard controller client, port: %d", port)
    DashboardControllerCLI("localhost", port).cmdloop()


if __name__ == "__main__":
    controller()

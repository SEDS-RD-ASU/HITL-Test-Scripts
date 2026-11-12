"""Contains the UART interface to communicate with the ASCENT board."""

import time
from logging import getLogger

import serial

logger = getLogger(name=__name__)


class ASCENT:
    """Class to handle UART communication with the ASCENT board."""

    def __init__(self, port: str, baudrate: int):
        """Initialize the UART interface.

        Args:
            port (str): The port to connect to the ASCENT board.
            baudrate (int): The baud rate for the UART communication.
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        logger.info(
            f"Initialized ASCENT UART interface on port {self.port} with baudrate {self.baudrate}."
        )
        self.connect()

    def connect(self):
        """Establish a connection to the ASCENT board."""
        self.serial_connection = serial.Serial(self.port, self.baudrate)

    def disconnect(self):
        """Close the connection to the ASCENT board."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

    def raw_send(self, command: bytes):
        """Send a command to the ASCENT board.

        Args:
            command (bytes): The command to send.
        """
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write(command)
            logger.debug(f"Sent command: {command.hex()}")

    def send_command(self, command: str):
        """Send a command to the ASCENT board.

        Args:
            command (str): The command to send.
        """
        self.raw_send(command.encode("utf-8"))

    def reset_board(self):
        """Pulse RTS to reset the board (assumes RTS is wired to NRST/EN via the adapter)."""
        if not self.serial_connection or not self.serial_connection.is_open:
            raise RuntimeError("No active serial connection.")
        logger.info("Resetting the ASCENT board.")

        self.serial_connection.dtr = (
            False  # GPIO0 high -> normal boot, not download mode
        )
        self.serial_connection.rts = True  # EN low -> chip held in reset
        time.sleep(0.1)  # Hold reset for 100ms
        self.serial_connection.rts = False  # EN high -> chip runs
        self.serial_connection.reset_input_buffer()

    def raw_response(self, bytes: int = 1024) -> bytes | None:
        """Read a response from the ASCENT board.

        Args:
            bytes (int): The number of bytes to read from the ASCENT board. Default is 1024.

        Returns:
            bytes: The response from the ASCENT board.
        """
        if self.serial_connection and self.serial_connection.is_open:
            data = self.serial_connection.read(bytes)
            if data:
                try:
                    text = data.decode("utf-8", errors="replace")
                except Exception:
                    text = data.hex()
                logger.debug(f"Received response: {text}")
            return data
        return None

    def read_response(self, bytes: int = 1024) -> str | None:
        """Read a response from the ASCENT board and decode it to a string.

        Args:
            bytes (int): The number of bytes to read from the ASCENT board. Default is 1024.

        Returns:
            str: The response from the ASCENT board as a string.
        """
        raw_response = self.raw_response(bytes)
        if raw_response:
            return raw_response.decode("utf-8")
        return None

    def wait_for_string(self, string:str, timeout: float = 10.0):
        """Wait for a specific string to be received from the ASCENT board.

        Args:
            string (str): The string to wait for.
            timeout (float): The maximum time to wait for the string, in seconds. Default is 10.0 seconds.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.read_response()
            if response and string in response:
                logger.info(f"Found expected string: {string}")
                return
            time.sleep(0.1)
        raise TimeoutError("Timed out waiting for the ASCENT board to be ready.")

    def reboot_to_data_loader(self):
        """Reboot the ASCENT board into data loader mode."""
        logger.info("Rebooting the ASCENT board into data loader mode.")
        self.send_command("reboot_to_data_loader")
        self.wait_for_string("app_main: USB_SERIAL_JTAG init done", timeout=20.0)
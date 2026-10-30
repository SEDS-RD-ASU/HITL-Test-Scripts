"""Contains the UART interface to communicate with the Assent board."""
import time
import serial


class Assent:
    """Class to handle UART communication with the Assent board."""

    def __init__(self, port: str, baudrate: int):
        """Initialize the UART interface.

        Args:
            port (str): The port to connect to the Assent board.
            baudrate (int): The baud rate for the UART communication.
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None

    def connect(self):
        """Establish a connection to the Assent board."""
        self.serial_connection = serial.Serial(self.port, self.baudrate)

    def disconnect(self):
        """Close the connection to the Assent board."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

    def raw_send(self, command: bytes):
        """Send a command to the Assent board.

        Args:
            command (bytes): The command to send.
        """
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write(command)

    def send_command(self, command: str):
        """Send a command to the Assent board.

        Args:
            command (str): The command to send.
        """
        self.raw_send(command.encode('utf-8'))

    def reset_board(self):
        """Pulse RTS to reset the board (assumes RTS is wired to NRST/EN via the adapter)."""
        if not self.serial_connection or not self.serial_connection.is_open:
            raise RuntimeError("No active serial connection.")

        self.serial_connection.dtr = False  # GPIO0 high -> normal boot, not download mode
        self.serial_connection.rts = True   # EN low -> chip held in reset
        time.sleep(0.1)  # Hold reset for 100ms
        self.serial_connection.rts = False  # EN high -> chip runs
        self.serial_connection.reset_input_buffer()

    def raw_response(self, bytes: int = 1024) -> bytes | None:
        """Read a response from the Assent board.

        Args:
            bytes (int): The number of bytes to read from the Assent board. Default is 1024.

        Returns:
            bytes: The response from the Assent board.
        """
        if self.serial_connection and self.serial_connection.is_open:
            return self.serial_connection.read(bytes)

    def read_response(self, bytes: int = 1024) -> str | None:
        """Read a response from the Assent board and decode it to a string.

        Args:
            bytes (int): The number of bytes to read from the Assent board. Default is 1024.

        Returns:
            str: The response from the Assent board as a string.
        """
        raw_response = self.raw_response(bytes)
        if raw_response:
            return raw_response.decode('utf-8')

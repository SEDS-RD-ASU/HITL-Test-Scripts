"""List all ports that can be used to connect to the Assent."""

import serial
import serial.tools.list_ports


def possible_ports():
    """Return a list of all ports that can be used to connect to Assent."""
    return serial.tools.list_ports.comports()

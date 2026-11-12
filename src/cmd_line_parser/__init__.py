import argparse
import pathlib

from src.send_fake_data.ASCENT_interface.get_ports import possible_ports

ports = possible_ports()
port_devices = [port.device for port in ports]
data_files = [
    str(path)
    for path in (
        pathlib.Path(__file__).parent.parent / "send_fake_data" / "sim_flight_data"
    ).iterdir()
    if path.is_file()
]

parser = argparse.ArgumentParser(
    prog="Hilt Test Suite",
    description="Tests an ASCENT board to see if the firmware is working properly.",
    epilog="2026 SEDS-RD HITL Test Suite - GPLv3 License",
)
parser.add_argument(
    "-p",
    "--port",
    type=str,
    choices=port_devices,
    default=port_devices[0] if port_devices else None,
    help="The port to connect to the ASCENT board on. If not specified, the program will attempt to find the port automatically.",
)
parser.add_argument(
    "--log-level",
    type=str,
    choices=["DEBUG", "INFO"],
    default="INFO",
    help="The log level to use for the program. Default is INFO.",
)
parser.add_argument(
    "--baudrate",
    type=int,
    default=115200,
    help="The baud rate to use for the UART communication. Default is 115200.",
)
parser.add_argument(
    "--data-path",
    type=str,
    choices=data_files,
    default=str(
        pathlib.Path(__file__).parent.parent
        / "send_fake_data"
        / "sim_flight_data"
        / "irec_200hz.csv"
    ),
    help="The path to the fake data file. Default is irec_200hz.csv.",
)

import argparse
import pathlib

from src.assent_interface.get_ports import possible_ports

parser = argparse.ArgumentParser(
    prog="Hilt Test Suite",
    description="Tests an assent board to see if the firmware is working properly.",
    epilog="2026 SEDS-RD HITL Test Suite - GPLv3 License",
)
parser.add_argument(
    "-p",
    "--port",
    type=str,
    choices=possible_ports(),
    default=possible_ports()[0].device if possible_ports() else None,
    help="The port to connect to the Assent board on. If not specified, the program will attempt to find the port automatically.",
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
    choices=[
        f
        for f in (
            pathlib.Path(__file__).parent.parent / "send_fake_data" / "sim_flight_data"
        ).iterdir()
        if f.is_file()
    ],
    default=pathlib.Path(__file__).parent.parent
    / "send_fake_data"
    / "sim_flight_data"
    / "irec_200hz.csv",
    help="The path to the fake data file. Default is irec_200hz.csv.",
)

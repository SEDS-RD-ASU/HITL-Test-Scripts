import argparse
import datetime
import os
import pathlib
import subprocess

from src.send_fake_data.ASCENT_interface.get_ports import possible_ports

SCRIPT_DIR = pathlib.Path(__file__).resolve().parents[2]


def default_dump_path() -> pathlib.Path:
    commit_id = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=SCRIPT_DIR,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    timestamp = datetime.datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    return pathlib.Path("dump") / f"bank_{commit_id}_{timestamp}.csv"


ports = possible_ports()
port_devices = [port.device for port in ports]

data_dir = pathlib.Path(__file__).parent.parent / "send_fake_data" / "sim_flight_data"
data_files = [str(path) for path in data_dir.iterdir() if path.is_file()]
default_data_path = data_dir / "scratchy_flight_data.csv" if (data_dir / "scratchy_flight_data.csv").exists() else data_files[0]

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
    default=921600,
    help="The baud rate to use for the UART communication. Default is 921600.",
)
parser.add_argument(
    "--data-path",
    type=pathlib.Path,
    default=default_data_path,
    help="The path to the fake data file. Defaults to scratchy_flight_data.csv.",
)
parser.add_argument(
    "--dump-path",
    type=pathlib.Path,
    default=default_dump_path(),
    help="The CSV path for the flash bank dump.",
)
parser.add_argument(
    "--dump-only",
    action="store_true",
    help="Only dump the latest bank and analyze it, skipping the upload of fake data.",
)
parser.add_argument(
    "--discord-webhook-url",
    type=str,
    help="The URL of the Discord webhook to send the run report to.",
    default=None
)
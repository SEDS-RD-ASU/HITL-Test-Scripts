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
legacy_data_dir = pathlib.Path(__file__).parent.parent / "send_fake_data" / "sim_flight_data"
data_files = [
    str(path)
    for path in legacy_data_dir.iterdir()
    if path.is_file()
]
sitl_dir = pathlib.Path(
    os.environ.get("SITL_DIR", str(SCRIPT_DIR.parent / "ascent-sitl"))
)
scratchy_data_path = sitl_dir / "sim_flight_data" / "scratchy_flight_data.csv"
if scratchy_data_path.is_file():
    data_files.append(str(scratchy_data_path))
default_data_path = (
    scratchy_data_path if scratchy_data_path.is_file()
    else legacy_data_dir / "packets_1_200hz.csv"
)

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
    help="Skip building, flashing, and data upload; only dump the latest bank.",
)

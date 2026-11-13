import re
import select
import struct
import subprocess
import time
from logging import getLogger
from pathlib import Path

import serial


FIRMWARE_DIR = "/home/hitl/ascent-r3-firmware"
IDF_ACTIVATE = "/home/hitl/.espressif/tools/activate_idf_v6.1.sh"
CSV_HEADER = "n, timestamp, bat_voltage"
CSV_HEADER_FULL = (
    "n, timestamp, bat_voltage, flight_state, pyro_cont, pressure, temperature, "
    "altitude_agl, ground_altitude, baro_vel, avg_baro_vel, UTCtstamp, lat, lon, "
    "altitude_ellipsoid, altitude_msl, fixType, num_sats, acc_x, acc_y, acc_z, "
    "hacc_x, hacc_y, hacc_z, gyr_x, gyr_y, gyr_z"
)
# Mirrors flash_packet in the firmware (see src/send_fake_data/upload.py).
FLASH_PACKET_FORMAT = "<QqfBB2xddddddIIIII BB2x fff fff fff 4x"
FLASH_PACKET_SIZE = struct.calcsize(FLASH_PACKET_FORMAT)
MONITOR_LINES_TO_READ = 4
DUMP_PROMPT_MARKER = "Enter the bank to dump (last bank used:"
PACKET_LOG_INTERVAL = 2_000
logger = getLogger(__name__)


def wait_for_monitor_start(port: str, timeout: float = 30.0) -> None:
    command = (
        f"source {IDF_ACTIVATE} && "
        f"idf.py -p {port} monitor"
    )
    logger.debug("Starting idf.py monitor on %s.", port)
    monitor = subprocess.Popen(
        ["bash", "-lc", command],
        cwd=FIRMWARE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    deadline = time.monotonic() + timeout

    try:
        for line_number in range(1, MONITOR_LINES_TO_READ + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for idf.py monitor output.")
            ready, _, _ = select.select([monitor.stdout], [], [], remaining)
            if not ready:
                raise TimeoutError("Timed out waiting for idf.py monitor output.")
            line = monitor.stdout.readline()
            if not line:
                raise RuntimeError("idf.py monitor exited before four lines were received.")
            logger.debug("idf.py monitor: %s", line.rstrip())
            logger.debug("Read monitor line %d/%d.", line_number, MONITOR_LINES_TO_READ)
    finally:
        logger.debug("Stopping idf.py monitor.")
        monitor.terminate()
        try:
            monitor.wait(timeout=5)
        except subprocess.TimeoutExpired:
            monitor.kill()
            monitor.wait()


def dump_latest_bank(port: str, baudrate: int, output_path: Path) -> None:
    wait_for_monitor_start(port)

    logger.debug("Opening UART %s at %d baud for flash dump.", port, baudrate)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with (
        output_path.open("w", encoding="utf-8", buffering=1) as output_file,
        serial.Serial(port, baudrate, timeout=0.1) as connection,
    ):
        logger.debug("Resetting board before listening for the dump dialog.")
        connection.dtr = False
        connection.rts = True
        time.sleep(0.1)
        connection.rts = False
        connection.reset_input_buffer()

        deadline = time.monotonic() + 30.0
        dump_requested = False
        bank = None

        while bank is None:
            if time.monotonic() >= deadline:
                raise TimeoutError("Timed out waiting for the firmware dump dialog.")
            line = connection.readline().decode("utf-8", errors="replace")
            if 'enter "DUMP"' in line:
                logger.debug("Firmware dump window detected; sending DUMP.")
                connection.write(b"DUMP\n")
                dump_requested = True
            match = re.search(r"last bank used: (-?\d+)", line)
            if dump_requested and match:
                bank = int(match.group(1))
                logger.debug("Selecting latest flash bank: %d.", bank)

        logger.debug("Requesting flash bank %d.", bank)
        connection.write(f"{bank}\n".encode("ascii"))

        deadline = time.monotonic() + 60.0
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("Timed out waiting for the binary dump to start.")
            line = connection.readline().decode("utf-8", errors="replace")
            match = re.search(r"BINARY DUMP START (\d+)", line)
            if match:
                break
        packet_size = int(match.group(1))
        if packet_size != FLASH_PACKET_SIZE:
            raise RuntimeError(
                f"Firmware packet size {packet_size} != expected {FLASH_PACKET_SIZE}."
            )

        output_file.write(CSV_HEADER_FULL + "\n")
        packet_count = 0
        deadline = time.monotonic() + 300.0
        while True:
            (length,) = struct.unpack("<I", _read_exact(connection, 4, deadline))
            if length == 0:
                break
            if length % packet_size:
                raise RuntimeError(f"Dump chunk of {length} bytes is not a whole number of packets.")
            chunk = _read_exact(connection, length, deadline)
            for fields in struct.iter_unpack(FLASH_PACKET_FORMAT, chunk):
                output_file.write(_format_row(fields))
                packet_count += 1
                if packet_count % PACKET_LOG_INTERVAL == 0:
                    logger.info("Downloaded %d flash packets.", packet_count)

    logger.info("Downloaded %d flash packets.", packet_count)
    logger.debug("Wrote %d packets to %s.", packet_count, output_path)


def _read_exact(connection: serial.Serial, size: int, deadline: float) -> bytes:
    data = bytearray()
    while len(data) < size:
        if time.monotonic() >= deadline:
            raise TimeoutError("Timed out waiting for the flash dump to finish.")
        data += connection.read(size - len(data))
    return bytes(data)


def _format_row(fields: tuple) -> str:
    # Same column order and formatting as the old firmware-side CSV (floats as %f).
    return ",".join(
        f"{value:.6f}" if isinstance(value, float) else str(value) for value in fields
    ) + "\n"

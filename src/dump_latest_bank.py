import re
import select
import subprocess
import time
from logging import getLogger
from pathlib import Path

import serial


FIRMWARE_DIR = "/home/hitl/ascent-r3-firmware"
IDF_ACTIVATE = "/home/hitl/.espressif/tools/activate_idf_v6.1.sh"
CSV_HEADER = "n, timestamp, bat_voltage"
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

        collecting = False
        packet_count = 0
        csv_line_count = 0

        deadline = time.monotonic() + 300.0
        while time.monotonic() < deadline:
            line = connection.readline().decode("utf-8", errors="replace")
            if not line:
                continue
            prompt_index = line.find(DUMP_PROMPT_MARKER) if collecting else -1
            finished_index = line.find("FINISHED DUMPING DATA") if collecting else -1
            end_index = min(
                (index for index in (prompt_index, finished_index) if index >= 0),
                default=-1,
            )
            if end_index >= 0:
                row_before_prompt = line[:end_index]
                if row_before_prompt:
                    output_file.write(row_before_prompt)
                    output_file.flush()
                logger.debug("Next dump prompt detected; stopping the current dump.")
                break
            if line.startswith(CSV_HEADER):
                collecting = True
                logger.debug("Flash dump CSV header received.")
            if collecting:
                output_file.write(line)
                output_file.flush()
                csv_line_count += 1
                if not line.startswith(CSV_HEADER):
                    packet_count += 1
                    if packet_count % PACKET_LOG_INTERVAL == 0:
                        logger.info("Downloaded %d flash packets.", packet_count)
        else:
            raise TimeoutError("Timed out waiting for the flash dump to finish.")

    if not collecting:
        raise RuntimeError("The firmware completed the dump without returning CSV data.")
    logger.info("Downloaded %d flash packets.", packet_count)
    logger.debug("Wrote %d CSV lines to %s.", csv_line_count, output_path)

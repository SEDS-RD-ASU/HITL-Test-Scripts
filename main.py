"""Main file that will run the full HITL Test suite."""

import logging
import os
import pathlib
import shlex
import subprocess
import sys

from src.cmd_line_parser import parser
from src.dump_latest_bank import dump_latest_bank
from src.run_report import create_run_report, send_run_report
from src.send_fake_data.ASCENT_interface import ASCENT
from src.send_fake_data.upload import upload_fake_data

if __name__ == "__main__":
    firmware_dir = pathlib.Path(
        os.environ.get("FIRMWARE_DIR", "/home/hitl/ascent-r3-firmware")
    )
    idf_activate = os.environ.get(
        "IDF_ACTIVATE_SCRIPT",
        "/home/hitl/.espressif/tools/activate_idf_v6.1.sh",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    if args.port is None:
        parser.error("No serial port was detected.")

    if args.dump_only:
        dump_latest_bank(
            args.port,
            args.baudrate,
            args.dump_path,
        )
        report = create_run_report(args.dump_path)
        send_run_report(*report)
        sys.exit(0)

    subprocess.run(
        ["sed", "-i", "s|^// #define SIMULATOR$|#define SIMULATOR|",
         str(firmware_dir / "main/main.c")],
        check=True,
    )
    subprocess.run(
        [
            "bash",
            "-lc",
            "grep -q '^#define DISABLE_BUZZER$' "
            f"{shlex.quote(str(firmware_dir / 'ascent-r3-drivers/indicator/src/driver_buzzer.c'))}"
            " || sed -i '1a #define DISABLE_BUZZER' "
            f"{shlex.quote(str(firmware_dir / 'ascent-r3-drivers/indicator/src/driver_buzzer.c'))}",
        ],
        check=True,
    )
    subprocess.run(
        [
            "bash",
            "-lc",
            f"source {shlex.quote(idf_activate)}"
            f" && idf.py -p {shlex.quote(args.port)} build flash",
        ],
        cwd=firmware_dir,
        check=True,
    )
    ascent = ASCENT(args.port, args.baudrate)
    upload_fake_data(ascent, args.data_path)
    ascent.disconnect()
    dump_latest_bank(
        args.port,
        args.baudrate,
        args.dump_path,
    )
    report = create_run_report(args.dump_path)
    send_run_report(*report)

    sys.exit(0)

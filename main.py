"""Main file that will run the full HITL Test suite."""

import logging
import sys

from src.cmd_line_parser import parser
from src.send_fake_data.ASCENT_interface import ASCENT
from src.send_fake_data.upload import upload_fake_data

if __name__ == "__main__":
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    upload_fake_data(ASCENT(args.port, args.baudrate), args.data_path)

    sys.exit(0)

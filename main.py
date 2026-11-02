"""Main file that will run the full HITL Test suite."""

from src.send_fake_data.assent_interface import Assent

import sys

from src.cmd_line_parser import parser
from src.send_fake_data.upload import upload_fake_data

if __name__ == "__main__":
    args = parser.parse_args()

    upload_fake_data(Assent(args.port, args.baudrate), args.data_path)

    sys.exit(0)

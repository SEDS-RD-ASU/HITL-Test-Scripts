"""Main file that will run the full HITL Test suite."""

import logging
import sys

from src import plots
from src.cmd_line_parser import parser
from src.discord_interaction.send_message import send_message
from src.send_fake_data.ASCENT_interface import ASCENT
from src.send_fake_data.extract_data import extract_data
from src.send_fake_data.upload import upload_fake_data

logger = logging.getLogger(name=__name__)

if __name__ == "__main__":
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )

    if args.port is None:
        parser.error("No serial port was detected.")
    
    ascent = ASCENT(args.port, args.baudrate)
    if not args.dump_only:
        logger.info("Uploading fake data...")
        upload_fake_data(ascent, args.data_path)

    logger.info("Extracting data from ASCENT board...")    
    data = extract_data(ascent)

    logger.info("Analyzing data")
    plots = [
        plots.delta_t(data),
    ]

    logger.info("Sending data to discord...")
    send_message(plot_paths=plots, skipped=-1, webhook_url=args.webhook_url)

    sys.exit(0)

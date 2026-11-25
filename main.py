"""Main file that will run the full HITL Test suite."""

import logging
import sys

from src.cmd_line_parser import parser
from src.discord_interaction.send_message import send_message
from src.plots import generate_plots
from src.send_fake_data.ASCENT_interface import ASCENT
from src.send_fake_data.extract_data import extract_data
from src.send_fake_data.upload import upload_fake_data
from src.test_requirements import run_test_scripts

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

    logger.info("Gathered the following columns from the ASCENT board:")
    for column in data.columns:
        logger.info(f" - {column} ({data[column].dtype})")

    logger.info("Checking test outputs...")
    tests_results = run_test_scripts(data)
    message = "\n".join(
        f"{test_name}: {'PASS' if result[0] else 'FAIL'}"
        + (f" - {result[1]}" if result[1] else "")
        for test_name, result in tests_results.items()
    )

    logger.info("Generating plots")
    plots = generate_plots(data)

    logger.info("Sending data to discord...")
    send_message(plot_paths=plots, message=message, skipped=-1, webhook_url=args.discord_webhook_url)

    sys.exit(0)

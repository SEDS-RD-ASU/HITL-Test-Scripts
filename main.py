""" Main file that will run the full HITL Test suite.

"""
import sys


if __name__ == "__main__":
    from src.cmd_line_parser import parser
    args = parser.parse_args()

    sys.exit(0)

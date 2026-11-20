# import pandas as pd

from .test__state_machine_stays_in_pad_state import (
    test__state_machine_stays_in_pad_state,
)

def run_test_scripts(data):
    # implement running test scripts here
    tests: dict[str, tuple[bool, str]] = {}

    # all tests should return a tuple[bool, str] for easy data parsing
    # if the test SUCCEEDS, entry should have (true, "")
    # if the test FAILS, entry should have (false, "Fail Reason")
    tests["State Machine stays in PAD State until 3g for 5ticks"] = (
        test__state_machine_stays_in_pad_state(data)
    )

    return tests

# import pandas as pd

from .test__state_machine_goes_to_boost_state import (
    test__state_machine_goes_to_boost_state,
)
from .test__state_machine_stays_in_pad_state import (
    test__state_machine_stays_in_pad_state,
)


def run_test_scripts(data):
    # all tests should return a tuple[bool, str] for easy data parsing
    # if the test SUCCEEDS, entry should have (true, "")
    # if the test FAILS, entry should have (false, "Fail Reason")
    tests: dict[str, tuple[bool, str]] = {
        "State Machine stays in PAD State until 3g for 5ticks": test__state_machine_stays_in_pad_state(
            data
        ),
        "State Machine goes to BOOST State at 3g for 5ticks": test__state_machine_goes_to_boost_state(
            data
        ),
    }

    return tests

"""State Machine stays in PAD State until 3g for 5ticks:

The state machine MUST remain locked in the PAD state and disable all pyrotechnic output drivers
until vertical acceleration exceeds the configured acceleration threshold (default = 3G) for a time
greater than the configured number of ticks (duration, default = 5)."""

from src.shared_types import FlightState

import pandas as pd


def test__state_machine_stays_in_pad_state(data: pd.DataFrame) -> tuple[bool, str]:
    accel_thres = 9.81 * 3
    num_ticks = 5

    # find the first index where the flight state is not PAD
    first_non_pad_index = data[
        data["flight_state"] != FlightState.FS_ON_PAD
    ].index.min()
    if first_non_pad_index is None:
        return (True, "Never left PAD state, test passed")

    # Get num ticks before the first non-PAD state
    start_index = max(0, first_non_pad_index - num_ticks)
    accel_data = data.loc[start_index:first_non_pad_index, "accel_z"]

    # Check if all accel_data values are above the threshold
    if (accel_data > accel_thres).all():
        return (
            True,
            "State machine left PAD state after exceeding acceleration threshold for required duration",
        )
    else:
        return (
            False,
            "State machine left PAD state before exceeding acceleration threshold for required duration",
        )

"""State Machine stays in PAD State until 3g for 5ticks:

The state machine MUST remain locked in the PAD state and disable all pyrotechnic output drivers
until vertical acceleration exceeds the configured acceleration threshold (default = 3G) for a time
greater than the configured number of ticks (duration, default = 5)."""

import pandas as pd

from src.shared_types import FlightState


def test__state_machine_stays_in_pad_state(data: pd.DataFrame) -> tuple[bool, str]:
    accel_thres = 9.81 * 3
    num_ticks = 5

    # find the first index where the flight state is not PAD
    first_non_pad_index = data[
        data["flight_state"] != FlightState.FS_ON_PAD
    ].index.min()
    if first_non_pad_index is None:
        return (True, "Never left PAD state, test passed")

    if first_non_pad_index < num_ticks:
        return (
            False,
            "State machine left PAD state before without enough ticks to check acceleration threshold",
        )

    # Get num ticks before the first non-PAD state
    start_index = first_non_pad_index - num_ticks
    accel_data = data.loc[start_index:first_non_pad_index, "acc_z"]

    # Check if all accel_data values are above the threshold
    if (accel_data > accel_thres).all():
        return (
            True,
            "",
        )
    else:
        return (
            False,
            f"State machine goes into Boost state before exceeding acceleration threshold for required duration. Last few ticks before Boost state: {accel_data.tolist()}",
        )

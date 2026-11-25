"""State Machine goes to BOOST State at 3g for 5ticks

The state machine MUST transition to BOOST only when vertical acceleration 
meets the configured acceleration threshold (default = 3G) 
for the configured number of ticks (duration, default = 5)."""

from src.shared_types import FlightState

import pandas as pd

def test__state_machine_stays_in_pad_state(data: pd.DataFrame) -> tuple[bool, str]:
    accel_thres = 9.81 * 3
    num_ticks = 5

    # find the first index where the flight state is not PAD
    first_boost_index = data[
        data["flight_state"] == FlightState.FS_BOOSTER
    ].index.min()
    if first_boost_index <= num_ticks:
        return (False, "Not enough ticks to compute test.")
    if first_boost_index is None:
        return (False, "Never goes into Boost state, test failed.")

    # Get num ticks before the first Boost state
    start_index = max(0, first_boost_index - num_ticks)
    accel_data = data.loc[start_index:first_boost_index, "accel_z"]

    # Check if all accel_data values are above the threshold
    if (accel_data > accel_thres).all():
        return (
            True,
            "State machine goes into Boost state after exceeding acceleration threshold for required duration",
        )
    else:
        return (
            False,
            "State machine goes into Boost state before exceeding acceleration threshold for required duration",
        )

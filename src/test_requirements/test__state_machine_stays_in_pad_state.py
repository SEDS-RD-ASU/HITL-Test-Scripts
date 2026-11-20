"""State Machine stays in PAD State until 3g for 5ticks:

The state machine MUST remain locked in the PAD state and disable all pyrotechnic output drivers 
until vertical acceleration exceeds the configured acceleration threshold (default = 3G) for a time 
greater than the configured number of ticks (duration, default = 5)."""
import pandas as pd


def test__state_machine_stays_in_pad_state(data: pd.DataFrame) -> tuple[bool, str]:
    accel_thres = 9.81*3
    num_ticks = 5
    
    return (False, "")


"""State Machine stays in PAD State until 3g for 5ticks:

The state machine MUST remain locked in the PAD state and disable all pyrotechnic output drivers 
until vertical acceleration exceeds the configured acceleration threshold (default = 3G) for a time 
greater than the configured number of ticks (duration, default = 5)."""
def test__state_machine_stays_in_pad_state(data) -> tuple[bool, str]:
    accel_thres = 9.81*3
    num_ticks = 5
    
    return (false, "")

def run_test_scripts(data):
    # implement running test scripts here
    tests:dict[str, tuple[bool, str]] = {}

    # all tests should return a tuple[bool, str] for easy data parsing
    # if the test SUCCEEDS, entry should have (true, "")
    # if the test FAILS, entry should have (false, "Fail Reason")
    tests["State Machine stays in PAD State until 3g for 5ticks"] = test__state_machine_stays_in_pad_state(data)

    return tests
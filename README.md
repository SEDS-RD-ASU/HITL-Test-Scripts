# HITL-Test-Scripts
Code that can run on a R-Pi connected to an ASCENT board to test ASCENT firmware.

Run `python main.py` to send the simulator data and save the latest flash bank
to `dump/bank_<commit>_<timestamp>.csv`. It defaults to
`ascent-sitl/sim_flight_data/scratchy_flight_data.csv`; use `--data-path` to
choose a different input or `--dump-path` to choose a different output path.

After each run, a Delta T plot is saved beside the dump and sent to the
Discord webhook in `DISCORD_WEBHOOK_URL`, along with the firmware commit link
and skipped packet count.

The GitHub Actions workflow runs on a self-hosted runner connected to the
ASCENT board. Configure the runner with the `hitl` label, add the
`DISCORD_WEBHOOK_URL` repository secret, and set the `HITL_PORT` repository
variable to the board's serial device.

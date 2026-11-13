# HITL-Test-Scripts
Code that can run on a R-Pi connected to an ASCENT board to test ASCENT firmware.

Run `python main.py` to send the simulator data and save the latest flash bank
to `dump/bank_<commit>_<timestamp>.csv`. It defaults to
`ascent-sitl/sim_flight_data/scratchy_flight_data.csv`; use `--data-path` to
choose a different input or `--dump-path` to choose a different output path.

The GitHub Actions workflow runs on a self-hosted runner connected to the
ASCENT board. Configure the runner with the `hitl` label, add the
`DISCORD_WEBHOOK_URL` repository secret, and set the `HITL_PORT` repository
variable to the board's serial device.

Uploading new firmware is out of the scope of this project. It expects to have 
whatever firmware being tested already on ASCENT, with the simulator enabled. 
If you are building new firmware, run `idf.py -DMAKE_SIMULATOR=1 build upload` beforehand.

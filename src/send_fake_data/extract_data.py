import logging
from dataclasses import asdict, fields

import pandas as pd

from src.send_fake_data.ASCENT_interface import ASCENT
from src.shared_types import FlightState, HITLData

logger = logging.getLogger(name=__name__)


def extract_data(ascent: ASCENT) -> pd.DataFrame:

    bank = ascent.reboot_to_data_extractor()
    ascent.send_command(f"{bank}");

    output: list[HITLData] = []

    # keep reading data (CSV) until we read "FINISHED DUMPING DATA"
    while True:
        line = ascent.read_response()
        if line is None:
            continue
        line = line.strip()
        if line == "FINISHED DUMPING DATA":
            break
        if line.startswith("n,timestamp,bat_voltage,flight_state,pyro_cont"):
            # skip the header line
            continue
        # parse the CSV line into a SimOutput object
        try:
            values = [float(x) for x in line.split(",")]
            record = HITLData(
                n=int(values[0]),
                timestamp=int(values[1]),
                bat_voltage=values[2],
                flight_state=FlightState(int(values[3])),
                pyro_cont=int(values[4]),
                pressure=values[5],
                temperature=values[6],
                altitude_agl=values[7],
                ground_altitude=values[8],
                baro_vel=values[9],
                avg_baro_vel=values[10],
                UTCtstamp=int(values[11]),
                lat=int(values[12]),
                lon=int(values[13]),
                altitude_ellipsoid=int(values[14]),
                altitude_msl=int(values[15]),
                fixType=int(values[16]),
                num_sats=int(values[17]),
                acc_x=values[18],
                acc_y=values[19],
                acc_z=values[20],
                hacc_x=values[21],
                hacc_y=values[22],
                hacc_z=values[23],
                gyr_x=values[24],
                gyr_y=values[25],
                gyr_z=values[26],
            )
            output.append(record)
        except Exception as e:
            logger.error(f"Failed to parse line: {line}. Error: {e}")

    return pd.DataFrame.from_records(
        [asdict(record) for record in output],
        columns=[field.name for field in fields(HITLData)],
    )

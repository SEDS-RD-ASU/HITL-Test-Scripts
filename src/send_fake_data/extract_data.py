import io
import logging
from dataclasses import asdict, fields

import pandas as pd

from src.send_fake_data.ASCENT_interface import ASCENT
from src.shared_types import FlightState, HITLData

logger = logging.getLogger(name=__name__)


def extract_data(ascent: ASCENT) -> pd.DataFrame:

    bank = ascent.reboot_to_data_extractor()
    ascent.send_command(f"{bank}");

    data = ""

    finished = False

    # keep reading data (CSV) until we read "FINISHED DUMPING DATA"
    while finished == False:
        line = ascent.read_response()
        if line is None:
            continue
        line = line.strip()
        if  "FINISHED DUMPING DATA" in line:
            line = line.replace("FINISHED DUMPING DATA", "")
            finished = True
        if line.startswith("n,timestamp,bat_voltage,flight_state,pyro_cont"):
            # skip the header line
            continue
        data += line

    # convert the string to a file-like object and read it as a CSV
    with io.StringIO(data) as f:
        df = pd.read_csv(f, header=0, names=[field.name for field in fields(HITLData)], skip_blank_lines=True)
        # convert all the columns to the correct type
        for field in fields(HITLData):
            if field.type == float:
                df[field.name] = df[field.name].astype(float)
            elif field.type == int:
                df[field.name] = df[field.name].astype(int)
            elif field.type == str:
                df[field.name] = df[field.name].astype(str)
            elif field.type == FlightState:
                df[field.name] = df[field.name].apply(lambda x: FlightState(x))
            else:
                raise ValueError(f"Unsupported type {field.type} for field {field.name}")
    logger.info(f"\nExtracted {len(df)} samples from ASCENT\n")
    logger.info(f"\nExtracted data:\n{df.head(100)}\n")
    return df
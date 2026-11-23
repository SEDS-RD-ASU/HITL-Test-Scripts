import io
import logging
from dataclasses import asdict, fields

import pandas as pd

from src.send_fake_data.ASCENT_interface import ASCENT
from src.shared_types import FlightState, HITLData

logger = logging.getLogger(name=__name__)


def extract_data(ascent: ASCENT) -> pd.DataFrame:

    bank = ascent.reboot_to_data_extractor()
    ascent.send_command(f"{bank}")

    data_lines = []
    buffer = ""
    finished = False

    # UART reads may contain partial rows or several rows at once.
    # Assemble complete newline-delimited rows before passing them to pandas.
    while not finished:
        chunk = ascent.read_response()
        if chunk is None:
            continue

        buffer += chunk
        if "FINISHED DUMPING DATA" in buffer:
            buffer = buffer.split("FINISHED DUMPING DATA", 1)[0]
            finished = True

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            if line.startswith("n,timestamp,bat_voltage,flight_state,pyro_cont"):
                continue
            data_lines.append(line)

    # convert the string to a file-like object and read it as a CSV
    column_names = [field.name for field in fields(HITLData)]
    with io.StringIO("\n".join(data_lines)) as f:
        df = pd.read_csv(
            f,
            header=None,
            names=column_names,
            skip_blank_lines=True,
        )
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
                raise ValueError(
                    f"Unsupported type {field.type} for field {field.name}"
                )
    logger.info(f"\nExtracted {len(df)} samples from ASCENT\n")
    logger.info(f"\nExtracted data:\n{df.head(100)}\n")
    return df

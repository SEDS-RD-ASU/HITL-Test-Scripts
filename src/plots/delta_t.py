from io import BytesIO
from typing import BinaryIO

import pandas as pd
from matplotlib import pyplot as plt

from src.shared_types import FlightState


def delta_t(all_data: pd.DataFrame) -> BinaryIO:
    """
    Create a graph of the time difference between consecutive timestamps in the data.
    The graph will be saved as a PNG file and the file object will be returned.
    """
    data = all_data.copy()
    data["delta_t"] = data["timestamp"].diff()
    data = data[["timestamp", "delta_t"]].dropna()
    state_changes = all_data[~all_data["flight_state"].duplicated()]

    plt.figure(figsize=(10, 5))
    plt.plot(data["timestamp"], data["delta_t"], marker="o", color="blue")

    # show all the flight state changes and the new state name
    for idx, row in state_changes.iterrows():
        plt.axvline(
            x=row["timestamp"],
            color="red",
            linestyle="--",
            alpha=0.5,
            label=f"{FlightState(row['flight_state']).name}",
        )

    plt.xlabel("Timestamp")
    plt.ylabel("Time Difference (ms)")
    plt.title("Delta T")
    plt.grid(True)

    # Save the plot to a BytesIO object
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png")
    img_buffer.seek(0)

    return img_buffer

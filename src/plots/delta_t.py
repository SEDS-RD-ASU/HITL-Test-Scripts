from io import BytesIO
from typing import BinaryIO

import pandas as pd
from matplotlib import pyplot as plt

from src.shared_types import FlightState

cmap = plt.get_cmap("tab10")


def delta_t(all_data: pd.DataFrame) -> BinaryIO:
    """
    Create a graph of the time difference between consecutive timestamps in the data.
    The graph will be saved as a PNG file and the file object will be returned.
    """
    data = all_data.copy()
    data["delta_t"] = data["timestamp"].diff()
    data = data[["timestamp", "delta_t"]].dropna()
    state_changes = all_data[~all_data["flight_state"].duplicated()]

    plt.figure(figsize=(11, 8.5))
    plt.plot(
        data["timestamp"],
        data["delta_t"],
        marker=".",
        color="black",
        linestyle="None",
        label="Delta T (ms)",
    )
    delta_t_mean = data["delta_t"].mean()
    delta_t_std = data["delta_t"].std()
    lower_bound = delta_t_mean - 1000
    upper_bound = delta_t_mean + 1000
    plt.ylim(lower_bound, upper_bound)
    plt.axhline(
        delta_t_mean,
        color="tab:red",
        linestyle="-",
        label=f"Mean: {delta_t_mean:.2f} ms",
    )
    for deviations in range(1, 4):
        for direction in (-1, 1):
            value = delta_t_mean + direction * deviations * delta_t_std
            sign = "-" if direction < 0 else "+"
            plt.axhline(
                value,
                color=cmap(deviations - 1),
                linestyle="--",
                alpha=0.6,
                label=f"Mean {sign} {deviations} SD: {value:.2f} ms",
            )
    upper_outliers = data[data["delta_t"] > upper_bound]
    lower_outliers = data[data["delta_t"] < lower_bound]
    edge_offset = (upper_bound - lower_bound) * 0.01
    if not upper_outliers.empty:
        plt.scatter(
            upper_outliers["timestamp"],
            [upper_bound - edge_offset] * len(upper_outliers),
            color="tab:red",
            marker="^",
            label=f"Outlier > mean + 1000 µs (n={len(upper_outliers)})",
            zorder=3,
        )
    if not lower_outliers.empty:
        plt.scatter(
            lower_outliers["timestamp"],
            [lower_bound + edge_offset] * len(lower_outliers),
            color="tab:red",
            marker="v",
            label=f"Outlier < mean - 1000 µs (n={len(lower_outliers)})",
            zorder=3,
        )

    # show all the flight state changes and the new state name
    for i, (idx, row) in enumerate(state_changes.iterrows()):
        plt.axvline(
            x=row["timestamp"],
            linestyle="--",
            alpha=0.5,
            color=cmap(i % cmap.N),
            label=f"{FlightState(row['flight_state']).name}",
        )

    plt.xlabel("Timestamp")
    plt.ylabel("Time Difference (µs)")
    plt.title("Delta T")
    plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    plt.grid(True)

    # Save the plot to a BytesIO object
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png", bbox_inches="tight")
    img_buffer.seek(0)

    return img_buffer

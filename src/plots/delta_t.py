from io import BytesIO
from typing import BinaryIO

import pandas as pd
from matplotlib import pyplot as plt


def delta_t(data: pd.DataFrame) -> BinaryIO:
    """
    Create a graph of the time difference between consecutive timestamps in the data.
    The graph will be saved as a PNG file and the file object will be returned.
    """
    data = data.copy()
    data['delta_t'] = data['timestamp'].diff().fillna(0)

    plt.figure(figsize=(10, 5))
    plt.plot(data['timestamp'], data['delta_t'], marker='o', linestyle='-', color='blue')
    plt.xlabel('Timestamp')
    plt.ylabel('Time Difference (ms)')
    plt.title('Delta T')
    plt.grid(True)

    # Save the plot to a BytesIO object
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer
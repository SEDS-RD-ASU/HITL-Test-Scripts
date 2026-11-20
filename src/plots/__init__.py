import pandas as pd

from .delta_t import delta_t


def generate_plots(data: pd.DataFrame):
    return [
        delta_t(data),
    ]
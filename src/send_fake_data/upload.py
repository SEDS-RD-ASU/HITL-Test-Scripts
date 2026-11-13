import os
import struct
import time
from logging import getLogger
from pathlib import Path

import numpy as np
import pandas as pd

from src.send_fake_data.ASCENT_interface import ASCENT

SEND_RATE_HZ = 1000

# ---------- flash_packet format ----------
# Layout:
#   uint64_t n; int64_t timestamp; float bat_voltage; uint8_t flight_state; uint8_t pyro_cont;
#   [2x pad]
#   double pressure, temperature, altitude_agl, ground_altitude, baro_vel, avg_baro_vel;
#   uint32_t UTCtstamp, lat, lon, altitude_ellipsoid, altitude_msl;
#   uint8_t fixType, num_sats; [2x pad]
#   float acc_x, acc_y, acc_z, hacc_x, hacc_y, hacc_z, gyr_x, gyr_y, gyr_z;
#   [4x pad]
FLASH_PACKET_FORMAT = "<QqfBB2xddddddIIIII BB2x fff fff fff 4x"
FLASH_PACKET_SIZE = struct.calcsize(FLASH_PACKET_FORMAT)

DELIMITER = b"\n\n\n\n"
PREPARE_COMMAND = b"PREPARE\n"

logger = getLogger(name=__name__)


def pack_row(idx, row) -> bytes:
    """Pack a single CSV row into a flash_packet bytestring."""
    if "n" in row:
        return struct.pack(
            FLASH_PACKET_FORMAT,
            int(row["n"]),
            int(row["timestamp"]),
            float(row["bat_voltage"]),
            int(row["flight_state"]),
            int(row["pyro_cont"]),
            float(row["pressure"]),
            float(row["temperature"]),
            float(row["altitude_agl"]),
            float(row["ground_altitude"]),
            float(row["baro_vel"]),
            float(row["avg_baro_vel"]),
            int(row["UTCtstamp"]),
            int(row["lat"]) & 0xFFFFFFFF,
            int(row["lon"]) & 0xFFFFFFFF,
            int(row["altitude_ellipsoid"]) & 0xFFFFFFFF,
            int(row["altitude_msl"]) & 0xFFFFFFFF,
            int(row["fixType"]),
            int(row["num_sats"]),
            float(row["acc_x"]),
            float(row["acc_y"]),
            float(row["acc_z"]),
            float(row["hacc_x"]),
            float(row["hacc_y"]),
            float(row["hacc_z"]),
            float(row["gyr_x"]),
            float(row["gyr_y"]),
            float(row["gyr_z"]),
        )

    return struct.pack(
        FLASH_PACKET_FORMAT,
        idx,  # n
        int(row["timestamp_s"] * 1e6),  # timestamp (µs)
        0.0,  # bat_voltage
        0,  # flight_state
        0,  # pyro_cont
        float(row["baro_press"]),  # pressure
        float(row["baro_temp"]),  # temperature
        float(row["baro_alt"]),  # altitude_agl
        0.0,  # ground_altitude
        0.0,  # baro_vel
        0.0,  # avg_baro_vel
        0,  # UTCtstamp
        int(row["latitude"]) & 0xFFFFFFFF,  # lat
        int(row["longitude"]) & 0xFFFFFFFF,  # lon
        0,  # alt_ellipsoid
        int(row["gps_altitude"]) & 0xFFFFFFFF,  # alt_msl
        0,  # fixType
        0,  # num_sats
        float(row["accx"]),  # acc_x
        float(row["accy"]),  # acc_y
        float(row["accz"]),  # acc_z
        float(row["haccx"]),  # hacc_x
        float(row["haccy"]),  # hacc_y
        float(row["haccz"]),  # hacc_z
        float(row["gyrx"]),  # gyr_x
        float(row["gyry"]),  # gyr_y
        float(row["gyrz"]),  # gyr_z
    )


def resample(df: pd.DataFrame, sample_times: list, rate_hz: float):
    """Resample to a fixed rate: floats are linearly interpolated, other columns hold the previous value."""
    t = np.asarray(sample_times, dtype=float)
    new_t = np.arange(t[0], t[-1], 1.0 / rate_hz)
    prev = np.searchsorted(t, new_t, side="right") - 1
    out = pd.DataFrame(
        {
            col: np.interp(new_t, t, df[col].to_numpy(dtype=float))
            if pd.api.types.is_float_dtype(df[col])
            else df[col].to_numpy()[prev]
            for col in df.columns
        }
    )
    if "timestamp_s" in out.columns:
        out["timestamp_s"] = new_t
    if "timestamp" in out.columns:
        out["timestamp"] = np.round(new_t * 1e6).astype(np.int64)
    if "n" in out.columns:
        out["n"] = np.arange(len(out)) + int(df["n"].iloc[0])
    return out, new_t.tolist()


def upload_fake_data(ASCENT: ASCENT, data_path: Path):
    """Uploads the fake data to ASCENT.

    Args:
        ASCENT (ASCENT): The ASCENT board interface.
        data (Path): The path to the fake data file.
    """
    df = pd.read_csv(data_path, skipinitialspace=True)
    df.columns = df.columns.str.strip()
    logger.info(f"\nLoaded {len(df)} samples from {os.path.basename(data_path)}\n")

    total = len(df)
    sample_times = (
        df["timestamp_s"].astype(float).tolist()
        if "timestamp_s" in df.columns
        else (df["timestamp"].astype(float) / 1e6).tolist()
    )
    df, sample_times = resample(df, sample_times, SEND_RATE_HZ)
    total = len(df)
    nominal_hz = SEND_RATE_HZ
    packets = [pack_row(idx, row) for idx, row in enumerate(df.to_dict("records"))]
    ASCENT.reboot_to_data_loader()
    ASCENT.raw_send(PREPARE_COMMAND)
    ASCENT.wait_for_string("SITL data is ready to enter flight computer", timeout=360.0) # erasing a bank takes lots of time :(
    t_start = time.perf_counter()

    for idx in range(total):
        # Preserve the source dataset's sample timing and avoid cumulative drift.
        target_time = t_start + sample_times[idx] - sample_times[0]

        now = time.perf_counter()
        sleep_time = target_time - now
        packet = packets[idx]
        if sleep_time > 0:
            time.sleep(sleep_time)
        ASCENT.raw_send(packet + DELIMITER)
        if idx % 100 == 0 or idx == total - 1:
            timestamp = (
                float(df.iloc[idx]["timestamp_s"])
                if "timestamp_s" in df.columns
                else float(df.iloc[idx]["timestamp"]) / 1e6
            )
            logger.info(
                f"\rSending sample {idx + 1}/{total} (t={timestamp:.4f}s)"
            )

    rate = f"{nominal_hz:.0f} Hz" if nominal_hz is not None else "source timing"
    logger.info(f"\nDone sending data. Sent {total} packets at {rate}.")

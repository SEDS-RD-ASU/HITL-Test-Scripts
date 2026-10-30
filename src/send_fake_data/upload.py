import os
import struct
import time
from logging import getLogger
from pathlib import Path

import pandas as pd

from src.assent_interface import Assent

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

SEND_HZ = 200
SEND_INTERVAL = 1.0 / SEND_HZ

logger = getLogger(name=__name__)


def pack_row(idx, row) -> bytes:
    """Pack a single CSV row into a flash_packet bytestring."""
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


def upload_fake_data(assent: Assent, data_path: Path):
    """Uploads the fake data to Assent.

    Args:
        assent (Assent): The Assent board interface.
        data (Path): The path to the fake data file.
    """
    assent.reset_board()
    df = pd.read_csv(data_path)
    logger.info(f"\nLoaded {len(df)} samples from {os.path.basename(data_path)}\n")

    total = len(df)
    t_start = time.perf_counter()

    for idx in range(total):
        # Schedule next send relative to start to avoid drift
        target_time = t_start + idx * SEND_INTERVAL

        now = time.perf_counter()
        sleep_time = target_time - now
        if sleep_time > 0:
            time.sleep(sleep_time)

        packet = pack_row(idx, df.iloc[idx])
        if idx % 100 == 0 or idx == total - 1:
            logger.info(
                f"\rSending sample {idx + 1}/{total} (t={df.iloc[idx]['timestamp_s']:.4f}s)"
            )
        assent.raw_send(packet + DELIMITER)

    logger.info(f"\nDone sending data. Sent {total} packets at {SEND_HZ} Hz.")

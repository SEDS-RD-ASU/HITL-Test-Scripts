import os
import struct
import time
from logging import getLogger
from pathlib import Path

import pandas as pd
from tqdm import tqdm

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
PREPARE_COMMAND = "PREPARE\n"

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
        time.time(),  # UTCtstamp
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
    total = len(df)
    packets = [pack_row(idx, row) for idx, row in enumerate(df.to_dict("records"))]
    ASCENT.reboot_to_data_loader()
    ASCENT.send_command(PREPARE_COMMAND)
    ASCENT.wait_for_string("SITL data is ready to enter flight computer", timeout=360.0) # erasing a bank takes lots of time :(
    t_start = time.perf_counter()

    for idx in tqdm(range(total), desc="Sending Data", mininterval=10, unit="dataframes"):
        # Preserve the source dataset's sample timing and avoid cumulative drift.
        target_time = t_start + sample_times[idx] - sample_times[0]
        sleep_time = target_time - time.perf_counter()

        packet = packets[idx]
        
        if sleep_time > 0:
            time.sleep(sleep_time)

        ASCENT.raw_send(packet + DELIMITER)
        ASCENT.wait_for_string("SITL ACK", timeout=1.0)


    logger.info(f"\nDone sending data. Sent {total} packets.")

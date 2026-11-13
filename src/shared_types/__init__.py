from dataclasses import dataclass
from enum import IntEnum


class FlightState(IntEnum):
    """Enum for flight states."""

    FS_ON_PAD = 0
    FS_BOOSTER = 1
    FS_COAST_BOOSTER = 2
    FS_SUSTAINER = 3
    FS_COAST_SUSTAINER = 4
    FS_UNDER_DROGUES = 5
    FS_UNDER_MAINS = 6
    FS_LANDED = 7
    FS_PREFLIGHT = 8


@dataclass
class HITLData:
    n: int
    timestamp: int
    bat_voltage: float
    flight_state: FlightState
    pyro_cont: int
    pressure: float
    temperature: float
    altitude_agl: float
    ground_altitude: float
    baro_vel: float
    avg_baro_vel: float
    UTCtstamp: int
    lat: int
    lon: int
    altitude_ellipsoid: int
    altitude_msl: int
    fixType: int
    num_sats: int
    acc_x: float
    acc_y: float
    acc_z: float
    hacc_x: float
    hacc_y: float
    hacc_z: float
    gyr_x: float
    gyr_y: float
    gyr_z: float
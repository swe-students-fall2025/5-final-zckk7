import os
from dataclasses import dataclass

@dataclass(frozen=True)
class SimConfig:
    mongodb_uri: str
    mongodb_db: str = "smart_apartment"
    interval_seconds: float = 2.0
    apartments: int = 8
    rooms_per_apartment: int = 3
    seed: int = 42

def load_config() -> SimConfig:
    uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017")
    db = os.getenv("MONGODB_DB", "smart_apartment")
    interval = float(os.getenv("SIM_INTERVAL_SECONDS", "2.0"))
    apts = int(os.getenv("SIM_APARTMENTS", "8"))
    rooms = int(os.getenv("SIM_ROOMS_PER_APT", "3"))
    seed = int(os.getenv("SIM_SEED", "42"))
    return SimConfig(
        mongodb_uri=uri,
        mongodb_db=db,
        interval_seconds=interval,
        apartments=apts,
        rooms_per_apartment=rooms,
        seed=seed,
    )
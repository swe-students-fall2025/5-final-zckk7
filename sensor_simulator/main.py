import time
import logging

from .config import load_config
from .generator import generate_batch
from .writer import get_db, ensure_indexes, write_readings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run_once(cfg=None, db=None, tick: int = 0) -> int:
    """
    Run one simulation tick: generate a batch and write to Mongo.
    Returns number of inserted docs.
    """
    if cfg is None:
        cfg = load_config()

    if db is None:
        db = get_db(cfg.mongodb_uri, cfg.mongodb_db)
        ensure_indexes(db)

    batch = generate_batch(cfg.apartments, cfg.rooms_per_apartment, cfg.seed + tick)
    n = write_readings(db, batch)
    logging.info("inserted=%s into sensor_readings", n)
    return n


def run_forever() -> None:
    cfg = load_config()
    db = get_db(cfg.mongodb_uri, cfg.mongodb_db)
    ensure_indexes(db)

    tick = 0
    while True:
        run_once(cfg=cfg, db=db, tick=tick)
        tick += 1
        time.sleep(cfg.interval_seconds)


if __name__ == "__main__":
    run_forever()
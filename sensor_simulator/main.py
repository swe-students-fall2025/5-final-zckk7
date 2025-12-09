import time
import logging

from .config import load_config
from .generator import generate_batch
from .writer import get_db, ensure_indexes, write_readings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def run_forever():
    cfg = load_config()
    db = get_db(cfg.mongodb_uri, cfg.mongodb_db)
    ensure_indexes(db)

    tick = 0
    while True:
        # Make it iterable
        batch = generate_batch(cfg.apartments, cfg.rooms_per_apartment, cfg.seed + tick)
        n = write_readings(db, batch)
        logging.info("inserted=%s into sensor_readings", n)
        tick += 1
        time.sleep(cfg.interval_seconds)

if __name__ == "__main__":
    run_forever()
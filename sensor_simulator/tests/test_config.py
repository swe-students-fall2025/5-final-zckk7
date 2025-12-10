from sensor_simulator.config import load_config

def test_load_config_reads_env(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://example:27017")
    monkeypatch.setenv("MONGODB_DB", "smart_apartment")
    monkeypatch.setenv("SIM_INTERVAL_SECONDS", "1.5")
    cfg = load_config()
    assert cfg.mongodb_uri == "mongodb://example:27017"
    assert cfg.mongodb_db == "smart_apartment"
    assert cfg.interval_seconds == 1.5
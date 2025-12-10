import sensor_simulator.main as main


def test_run_once_calls_writer_and_returns_count(monkeypatch):
    class Cfg:
        mongodb_uri = "mongodb://example"
        mongodb_db = "smart_apartment"
        interval_seconds = 2.0
        apartments = 1
        rooms_per_apartment = 1
        seed = 42

    monkeypatch.setattr(main, "load_config", lambda: Cfg)

    monkeypatch.setattr(main, "generate_batch", lambda a, r, s: [{"x": 1}])
    monkeypatch.setattr(main, "get_db", lambda uri, db: object())
    monkeypatch.setattr(main, "ensure_indexes", lambda db: None)
    monkeypatch.setattr(main, "write_readings", lambda db, batch: 123)

    assert main.run_once() == 123
from pathlib import Path

from app.core.paths import resolve_data_path, resolve_data_root


def test_resolve_data_root_defaults_to_repo_data() -> None:
    resolve_data_root.cache_clear()

    data_root = resolve_data_root()

    assert data_root.name == "data"
    assert data_root.exists()
    assert resolve_data_path("examples", "reports.jsonl").exists()


def test_resolve_data_root_respects_env_override(monkeypatch) -> None:
    override = Path("/tmp/pancreatic-signal-test-data")
    monkeypatch.setenv("PANCREATIC_SIGNAL_DATA_DIR", str(override))
    resolve_data_root.cache_clear()

    assert resolve_data_root() == override.resolve()

    monkeypatch.delenv("PANCREATIC_SIGNAL_DATA_DIR", raising=False)
    resolve_data_root.cache_clear()

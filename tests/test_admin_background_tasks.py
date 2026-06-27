import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import config
import database


class FakeCursor:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return {"total": 42}


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor

    def cursor(self):
        return self.cursor_instance


def test_write_background_analysis_config_inserts_before_hf_daily(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "presence:",
                "  snapshot_interval_seconds: 60",
                "",
                "hf_daily:",
                "  enabled: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    config.write_background_analysis_config(enabled=True, check_interval_seconds=300)

    updated = config_path.read_text(encoding="utf-8")
    assert "presence:\n  snapshot_interval_seconds: 60\n\nbackground_analysis:" in updated
    assert "  enabled: true\n  check_interval_seconds: 300\n\nhf_daily:" in updated


def test_write_background_analysis_config_replaces_existing_section(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "\n".join(
            [
                "background_analysis:",
                "  enabled: true",
                "  check_interval_seconds: 120",
                "",
                "hf_daily:",
                "  enabled: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "CONFIG_PATH", config_path)

    config.write_background_analysis_config(enabled=False, check_interval_seconds=600)

    updated = config_path.read_text(encoding="utf-8")
    background_section = updated.split("hf_daily:", 1)[0]
    assert "  enabled: true" not in background_section
    assert "  enabled: false\n  check_interval_seconds: 600" in updated
    assert "hf_daily:\n  enabled: true" in updated


def test_count_unanalyzed_papers_counts_null_llm_responses(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def fake_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(database, "DATABASE_URL", "postgresql://test/paper_online")
    monkeypatch.setattr(database, "_get_connection", fake_get_connection)

    total = database.count_unanalyzed_papers()

    assert total == 42
    sql, params = cursor.calls[0]
    assert "COUNT(*) AS total" in sql
    assert "llm_response IS NULL" in sql
    assert params is None


def test_count_papers_counts_all_papers(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def fake_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(database, "DATABASE_URL", "postgresql://test/paper_online")
    monkeypatch.setattr(database, "_get_connection", fake_get_connection)

    total = database.count_papers()

    assert total == 42
    sql, params = cursor.calls[0]
    assert "COUNT(*) AS total" in sql
    assert "FROM papers" in sql
    assert params is None


def test_count_unchecked_code_availability_counts_null_checked_at(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def fake_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(database, "DATABASE_URL", "postgresql://test/paper_online")
    monkeypatch.setattr(database, "_get_connection", fake_get_connection)

    total = database.count_unchecked_code_availability()

    assert total == 42
    sql, params = cursor.calls[0]
    assert "COUNT(*) AS total" in sql
    assert "code_checked_at IS NULL" in sql
    assert params is None

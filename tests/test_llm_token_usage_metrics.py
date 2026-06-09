import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import database


class FakeCursor:
    def __init__(self, rows=None):
        self.calls = []
        self.rows = rows or []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True


def test_record_llm_token_usage_inserts_normalized_totals(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)

    @contextmanager
    def fake_get_connection():
        yield connection

    monkeypatch.setattr(database, "DATABASE_URL", "postgresql://example")
    monkeypatch.setattr(database, "_get_connection", fake_get_connection)

    database.record_llm_token_usage(
        provider_id="11111111-1111-1111-1111-111111111111",
        provider_key="step",
        provider_name="Step",
        model_name="step-test",
        request_type="chat",
        input_tokens=12,
        output_tokens=5,
        cache_input_tokens=2,
        cache_output_tokens=3,
    )

    query, params = cursor.calls[0]
    assert "INSERT INTO llm_token_usage" in query
    assert params[:10] == (
        "11111111-1111-1111-1111-111111111111",
        "step",
        "Step",
        "step-test",
        "chat",
        12,
        5,
        2,
        3,
        17,
    )
    assert connection.committed is True


def test_build_llm_usage_window_returns_daily_and_model_aggregates():
    tz = ZoneInfo("UTC")
    today = datetime.now(tz).date()
    rows = [
        {
            "usage_date": today,
            "provider_key": "step",
            "provider_name": "Step",
            "model_name": "step-test",
            "request_count": 2,
            "input_tokens": 120,
            "output_tokens": 30,
            "cache_input_tokens": 18,
            "cache_output_tokens": 42,
            "total_tokens": 150,
        },
        {
            "usage_date": today - timedelta(days=1),
            "provider_key": "openrouter",
            "provider_name": "OpenRouter",
            "model_name": "router-test",
            "request_count": 1,
            "input_tokens": 80,
            "output_tokens": 20,
            "cache_input_tokens": 0,
            "cache_output_tokens": 10,
            "total_tokens": 100,
        },
    ]

    window = database._build_llm_usage_window(7, rows, tz)

    assert len(window["days"]) == 7
    assert window["totals"] == {
        "request_count": 3,
        "input_tokens": 200,
        "output_tokens": 50,
        "cache_input_tokens": 18,
        "cache_output_tokens": 52,
        "total_tokens": 250,
    }
    assert window["daily_totals"][-1]["date"] == today.isoformat()
    assert window["daily_totals"][-1]["total_tokens"] == 150
    assert window["model_totals"][0]["model_name"] == "step-test"
    assert window["model_totals"][0]["cache_output_tokens"] == 42
    assert window["daily"][0]["date"] == today.isoformat()

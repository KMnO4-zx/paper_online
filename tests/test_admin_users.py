import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

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
        return {"total": 2}

    def fetchall(self):
        return [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "email": "online@example.com",
                "role": "user",
                "is_active": True,
                "email_verified": True,
                "created_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
                "last_login_at": datetime(2026, 6, 8, tzinfo=timezone.utc),
                "is_online": True,
                "online_last_seen_at": datetime(2026, 6, 8, 12, tzinfo=timezone.utc),
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "email": "offline@example.com",
                "role": "admin",
                "is_active": True,
                "email_verified": True,
                "created_at": datetime(2026, 5, 1, tzinfo=timezone.utc),
                "last_login_at": None,
                "is_online": False,
                "online_last_seen_at": None,
            },
        ]


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_instance = cursor

    def cursor(self):
        return self.cursor_instance


def install_fake_connection(monkeypatch, cursor):
    @contextmanager
    def fake_get_connection():
        yield FakeConnection(cursor)

    monkeypatch.setattr(database, "_get_connection", fake_get_connection)


def test_list_users_includes_online_state_and_orders_online_first(monkeypatch):
    cursor = FakeCursor()
    install_fake_connection(monkeypatch, cursor)

    users, total = database.list_users(search=None, offset=0, limit=10)

    assert total == 2
    assert [user["email"] for user in users] == ["online@example.com", "offline@example.com"]
    assert users[0]["is_online"] is True
    assert users[0]["online_last_seen_at"] == datetime(2026, 6, 8, 12, tzinfo=timezone.utc)
    assert users[1]["is_online"] is False

    list_sql = cursor.calls[1][0]
    assert "WITH active_presence AS" in list_sql
    assert "MAX(last_seen_at) AS online_last_seen_at" in list_sql
    assert "(active_presence.user_id IS NOT NULL) DESC" in list_sql


def test_list_users_can_order_by_created_at(monkeypatch):
    cursor = FakeCursor()
    install_fake_connection(monkeypatch, cursor)

    database.list_users(search=None, offset=0, limit=10, sort_by="created_at", sort_direction="asc")

    list_sql = cursor.calls[1][0]
    assert "ORDER BY u.created_at ASC, u.email ASC" in list_sql


def test_list_users_can_order_by_last_login_at(monkeypatch):
    cursor = FakeCursor()
    install_fake_connection(monkeypatch, cursor)

    database.list_users(search=None, offset=0, limit=10, sort_by="last_login_at", sort_direction="desc")

    list_sql = cursor.calls[1][0]
    assert "ORDER BY u.last_login_at DESC NULLS LAST, u.created_at DESC, u.email ASC" in list_sql


def test_list_users_can_order_offline_first(monkeypatch):
    cursor = FakeCursor()
    install_fake_connection(monkeypatch, cursor)

    database.list_users(search=None, offset=0, limit=10, sort_by="online", sort_direction="asc")

    list_sql = cursor.calls[1][0]
    assert "ORDER BY (active_presence.user_id IS NOT NULL) ASC" in list_sql

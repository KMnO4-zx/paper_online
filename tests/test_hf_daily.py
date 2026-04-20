import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from hf_daily import select_top_hf_daily_entries


def test_select_top_hf_daily_entries_sorts_and_deduplicates_by_upvotes():
    entries = [
        {
            "paper": {
                "id": "2604.00001",
                "title": "Low Vote Paper",
                "summary": "Summary",
                "upvotes": 1,
                "authors": [{"name": "Alice"}],
                "ai_keywords": ["rl"],
            },
            "thumbnail": "https://example.com/1.png",
            "numComments": 2,
        },
        {
            "paper": {
                "id": "2604.00002",
                "title": "High Vote Paper",
                "summary": "Summary",
                "upvotes": 10,
                "authors": [{"name": "Bob"}],
                "ai_keywords": ["vision"],
                "githubRepo": "https://github.com/example/repo",
                "githubStars": 42,
            },
            "numComments": 4,
        },
        {
            "paper": {
                "id": "2604.00001",
                "title": "Low Vote Paper Updated",
                "summary": "Updated",
                "upvotes": 5,
                "authors": [{"name": "Alice"}],
                "ai_keywords": ["updated"],
            },
        },
    ]

    selected = select_top_hf_daily_entries(entries, top_n=2)

    assert [entry["source_id"] for entry in selected] == ["2604.00002", "2604.00001"]
    assert [entry["daily"]["rank"] for entry in selected] == [1, 2]
    assert selected[0]["paper"]["id"] == "hf:2604.00002"
    assert selected[0]["paper"]["pdf"] == "https://arxiv.org/pdf/2604.00002"
    assert selected[0]["paper"]["venue"] == "Hugging Face Daily"
    assert selected[0]["daily"]["github_repo"] == "https://github.com/example/repo"
    assert selected[0]["daily"]["github_stars"] == 42
    assert selected[1]["paper"]["title"] == "Low Vote Paper Updated"
    assert selected[1]["paper"]["primary_area"] == "HF Daily Top 2"


def test_select_top_hf_daily_entries_skips_invalid_entries():
    selected = select_top_hf_daily_entries(
        [
            {"paper": {"id": "", "title": "Missing ID"}},
            {"paper": {"id": "2604.00003", "title": ""}},
            {"not_paper": {}},
        ],
        top_n=5,
    )

    assert selected == []

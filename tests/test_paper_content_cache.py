from pathlib import Path
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import utils


def test_cache_round_trip_uses_paper_id_and_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_CONTENT_CACHE_DIR", str(tmp_path))

    paper_id = "paper/with:unsafe?chars"
    pdf_url = "https://example.com/paper.pdf"
    content = "cached paper body"

    utils.cache_paper_content(paper_id, pdf_url, content)

    txt_files = list(tmp_path.glob("*.txt"))
    meta_files = list(tmp_path.glob("*.meta.json"))

    assert len(txt_files) == 1
    assert len(meta_files) == 1
    assert utils.has_cached_paper_content(paper_id, pdf_url) is True
    assert utils.get_cached_paper_content(paper_id, pdf_url) == content

    metadata = json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert metadata["paper_id"] == paper_id
    assert metadata["pdf_url"] == pdf_url
    assert metadata["source"] == "jina_reader"


def test_get_or_cache_paper_content_hits_reader_once(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_CONTENT_CACHE_DIR", str(tmp_path))

    calls: list[str] = []

    def fake_reader(url: str) -> str:
        calls.append(url)
        return "body from reader"

    monkeypatch.setattr(utils, "reader", fake_reader)

    paper_id = "uq6UWRgzMr"
    pdf_url = "https://example.com/uq6UWRgzMr.pdf"

    first = utils.get_or_cache_paper_content(paper_id, pdf_url)
    second = utils.get_or_cache_paper_content(paper_id, pdf_url)

    assert first == "body from reader"
    assert second == "body from reader"
    assert calls == [pdf_url]

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from prompt import build_open_in_ai_prompt


def test_build_open_in_ai_prompt_includes_pdf_url():
    prompt = build_open_in_ai_prompt("https://example.com/paper.pdf")

    assert "https://example.com/paper.pdf" in prompt
    assert "论文 PDF 链接：" in prompt
    assert "{pdf_url}" not in prompt

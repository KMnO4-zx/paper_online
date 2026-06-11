import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from analysis_context import build_analysis_prompt, build_chat_context_parts


def test_build_analysis_prompt_uses_full_content_when_available():
    prompt = build_analysis_prompt({"title": "Paper"}, "full paper text")

    assert prompt == "以下是论文内容：\nfull paper text"


def test_build_analysis_prompt_falls_back_to_metadata_without_inventing():
    paper = {
        "title": "A CHI Paper",
        "venue": "CHI 2026",
        "primary_area": "Religion, Spirituality, and Design",
        "authors": ["A", "B"],
        "keywords": ["Religion", "Social media"],
        "pdf": "https://dl.acm.org/doi/pdf/10.1145/3772318.3791732",
        "abstract": "This is an abstract.",
    }

    prompt = build_analysis_prompt(paper, None, "目标页面被访问验证或反爬拦截")

    assert "只基于这些信息做初筛分析" in prompt
    assert "不要编造" in prompt
    assert "A CHI Paper" in prompt
    assert "This is an abstract." in prompt
    assert "目标页面被访问验证或反爬拦截" in prompt


def test_build_chat_context_parts_falls_back_to_metadata():
    parts = build_chat_context_parts({"title": "A CHI Paper", "abstract": "Abstract"}, None, "blocked")

    assert len(parts) == 1
    assert "论文元数据" in parts[0]
    assert "A CHI Paper" in parts[0]

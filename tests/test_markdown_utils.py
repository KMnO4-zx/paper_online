from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from markdown_utils import normalize_llm_markdown


def test_normalize_llm_markdown_repairs_markdown_and_math():
    normalized = normalize_llm_markdown(
        "\\#Heading\n\\(x_i\\)\n\\[\n\\frac{1}{2}\n\\]\n1)First item",
        analysis_mode=True,
    )

    assert "# Heading" in normalized
    assert "$x_i$" in normalized
    assert "$$\n\\frac{1}{2}\n$$" in normalized
    assert "1) First item" in normalized


def test_normalize_llm_markdown_keeps_code_blocks_literal():
    content = "```python\nvalue = '$x$'\n```"

    assert normalize_llm_markdown(content) == content


def test_normalize_llm_markdown_splits_inline_heading_fragments():
    normalized = normalize_llm_markdown(
        "开源代码仓库链接：https://github.com/lasr-spelling/sae-spelling # 问题1：论文要解决什么任务？",
        analysis_mode=True,
    )

    assert (
        "开源代码仓库链接：https://github.com/lasr-spelling/sae-spelling\n\n# 问题1：论文要解决什么任务？"
        in normalized
    )

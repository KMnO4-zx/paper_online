import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "build_cvpr_2026_jsonl.py"
SPEC = importlib.util.spec_from_file_location("build_cvpr_2026_jsonl", SCRIPT_PATH)
assert SPEC and SPEC.loader
cvpr = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cvpr
SPEC.loader.exec_module(cvpr)


LIST_SAMPLE = """
<dl>
<dt class="ptitle"><br><a href="/content/CVPR2026/html/Xiao_Test_Title_CVPR_2026_paper.html">Test Title</a></dt>
<dt class="ptitle"><br><a href="/content/CVPR2026/html/Chen_Another_Title_CVPR_2026_paper.html">Another Title</a></dt>
</dl>
"""


DETAIL_SAMPLE = """
<html><head>
<meta name="citation_title" content="Test Title">
<meta name="citation_author" content="Xiao, Jie">
<meta name="citation_author" content="Ma, Yinchao">
<meta name="citation_firstpage" content="1">
<meta name="citation_lastpage" content="11">
<meta name="citation_pdf_url" content="https://openaccess.thecvf.com/content/CVPR2026/papers/Xiao_Test_Title_CVPR_2026_paper.pdf">
</head><body>
<div id="content"><dl>
<div id="papertitle">Test Title</div>
<div id="authors"><br><b><i>Jie Xiao, Yinchao Ma</i></b>; Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2026, pp. 1-11</div>
<div id="abstract">This paper tests the parser.</div>
[<a href="/content/CVPR2026/papers/Xiao_Test_Title_CVPR_2026_paper.pdf">pdf</a>]
[<a href="/content/CVPR2026/supplemental/Xiao_Test_Title_CVPR_2026_supplemental.pdf">supp</a>]
<div class="bibref pre-white-space">@InProceedings{Xiao_2026_CVPR}</div>
</dl></div>
</body></html>
"""


def test_parse_cvf_list_preserves_official_order():
    links = cvpr.parse_cvf_list(LIST_SAMPLE)

    assert [link.order for link in links] == [1, 2]
    assert links[0].html_url == "https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_Test_Title_CVPR_2026_paper.html"


def test_parse_cvf_detail_and_jsonl_record_shape():
    link = cvpr.CvfPaperLink(
        order=7,
        html_url="https://openaccess.thecvf.com/content/CVPR2026/html/Xiao_Test_Title_CVPR_2026_paper.html",
    )
    detail = cvpr.parse_cvf_detail(link, DETAIL_SAMPLE)

    assert detail["order"] == 7
    assert detail["title"] == "Test Title"
    assert detail["authors"] == ["Jie Xiao", "Yinchao Ma"]
    assert detail["abstract"] == "This paper tests the parser."
    assert detail["pdf"] == "https://openaccess.thecvf.com/content/CVPR2026/papers/Xiao_Test_Title_CVPR_2026_paper.pdf"
    assert detail["supplemental"].endswith("_supplemental.pdf")
    assert detail["pages"] == "1-11"

    record = cvpr.build_jsonl_record(detail)
    assert record["id"].startswith("cvpr2026-xiao-test-title-")
    assert record["content"]["venue"]["value"] == "CVPR 2026"
    assert record["content"]["primary_area"]["value"] == "Computer Vision and Pattern Recognition"
    assert record["content"]["sort_order"]["value"] == 7

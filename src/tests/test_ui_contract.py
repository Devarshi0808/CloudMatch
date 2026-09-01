from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_ui_uses_one_research_request_and_one_evidence_set():
    script = (ROOT / "public" / "react-app.js").read_text()
    assert script.count('fetch("/api/research"') == 1
    assert 'fetch("/api/search"' not in script
    assert "brief.evidence" in script


def test_ui_exposes_quality_controls_and_bounded_snippets():
    script = (ROOT / "public" / "react-app.js").read_text()
    styles = (ROOT / "public" / "react-app.css").read_text()
    assert "duplicates removed" in script
    assert "low-quality filtered" in script
    assert "free-plan credit" in script
    assert "quality?.search_depth" in script
    assert "-webkit-line-clamp: 4" in styles

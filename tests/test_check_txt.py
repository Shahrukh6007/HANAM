from pathlib import Path


def test_check_txt_says_hello():
    path = Path(__file__).parent.parent / "workspace" / "check.txt"
    content = path.read_text(encoding="utf-8")
    assert "hello" in content, f"Expected 'hello', got: {content!r}"
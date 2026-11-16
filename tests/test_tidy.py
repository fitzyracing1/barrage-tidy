"""Tests for barrage-tidy. Official example copied from fitzyracing1/barrage."""

from __future__ import annotations

from pathlib import Path

from barrage_tidy.checker import REQUIRED_SECTIONS, check_text
from barrage_tidy.cli import main
from barrage_tidy.tidy import tidy

SAMPLES = Path(__file__).parent / "samples"


def test_official_example_stays_valid():
    source = (SAMPLES / "reset-and-count.official.barrage").read_text(encoding="utf-8")
    assert check_text(source) == []
    result = tidy(source)
    assert check_text(result.source) == []
    assert "# Reset and Count" in result.source
    assert "## How it works (plain English)" in result.source
    assert "```" in result.source
    assert "if (n <= 0)" in result.source


def test_rough_notes_become_valid_document():
    source = (SAMPLES / "rough-notes.barrage").read_text(encoding="utf-8")
    assert check_text(source)  # incomplete on purpose
    result = tidy(source)
    errors = check_text(result.source)
    assert errors == []
    text = result.source
    assert text.startswith("# Reset and Count")
    assert "> " in text
    assert "## Purpose" in text
    assert "Stop an important number from becoming invalid." in text
    assert "## How it works (plain English)" in text
    assert "## The actual code" in text
    assert "```" in text
    assert "if (n <= 0)" in text
    assert "## Current status" in text
    assert "Unfinished core logic" in text
    # Leftover prose that could not be mapped is an HTML comment.
    assert "<!-- BARRAGE-TODO:" in text
    assert "random leftover thought" in text
    kinds = {c.kind for c in result.changes}
    assert "todo" in kinds
    assert "placeholder" in kinds  # missing official sections get placeholders
    assert "check" in kinds


def test_bare_code_is_fenced():
    source = "Guard\n\nif (n <= 0) {\n    n = 0;\n}\n"
    result = tidy(source)
    assert check_text(result.source) == []
    assert "```" in result.source
    assert "n = 0;" in result.source


def test_unknown_heading_becomes_todo_comment():
    source = "# Demo\n\n> A short summary for anyone who is reading this draft document.\n\n## Mystery section\nsecret sauce\n"
    result = tidy(source)
    assert "<!-- BARRAGE-TODO:" in result.source
    assert "Mystery section" in result.source
    assert check_text(result.source) == []


def test_cli_write_does_not_overwrite(tmp_path, capsys):
    src = tmp_path / "notes.barrage"
    original = (SAMPLES / "rough-notes.barrage").read_text(encoding="utf-8")
    src.write_text(original, encoding="utf-8")
    assert main([str(src), "--write"]) == 0
    assert src.read_text(encoding="utf-8") == original
    dest = tmp_path / "notes.tidy.barrage"
    assert dest.is_file()
    assert check_text(dest.read_text(encoding="utf-8")) == []
    err = capsys.readouterr().err
    assert "Wrote" in err
    assert "official Barrage required structure" in err


def test_vendored_rules_match_official_package_when_installed():
    try:
        from barrage_checker.checker import REQUIRED_SECTIONS as official
    except ImportError:
        return
    assert list(REQUIRED_SECTIONS) == list(official)

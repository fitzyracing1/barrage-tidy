"""Vendored copy of the official Barrage document checks.

Mirrors fitzyracing1/barrage-checker 1.0.0 (barrage_checker/checker.py) so
this helper can validate output offline without a second package. The
required section patterns are the official ones from SPEC.md / barrage-checker;
none were invented here.
"""

from __future__ import annotations

import re
from pathlib import Path

# Identical to barrage_checker.checker.REQUIRED_SECTIONS in barrage-checker 1.0.0.
REQUIRED_SECTIONS = [
    r"^# .+",  # Title
    r"^> .+",  # Summary quote
    r"^## Purpose",
    r"^## How it works \(plain English\)",
    r"^## Key ideas",
    r"^## The actual code",
    r"^## Line-by-line translation",
    r"^## Decisions the program makes",
    r"^## What a person would notice",
    r"^## Current status",
    r"^## Next possible steps",
]


def check_text(text: str) -> list[str]:
    """Return error messages; an empty list means the document is valid."""
    errors: list[str] = []
    for pattern in REQUIRED_SECTIONS:
        if not re.search(pattern, text, re.MULTILINE):
            errors.append(f"Missing required section matching: {pattern}")
    if "```" not in text:
        errors.append("No code fence found — original code must be present")
    if len(text.strip()) < 200:
        errors.append("Document is very short — may be incomplete")
    return errors


def check_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Could not read file: {exc}"]
    return check_text(text)

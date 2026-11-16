"""Turn rough notes into a Barrage document that follows SPEC.md v1.0.

Only official section names from https://github.com/fitzyracing1/barrage
are written. Unfixable leftover lines become HTML comments, which is the
comment form Barrage inherits from its Markdown-like structure
(SPEC.md §2: "similar to Markdown"). No Barrage keywords are invented.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from barrage_tidy.checker import check_text

# Official required headings, in the required order (SPEC.md §3).
REQUIRED_HEADINGS = [
    "Purpose",
    "How it works (plain English)",
    "Key ideas",
    "The actual code",
    "Line-by-line translation",
    "Decisions the program makes",
    "What a person would notice",
    "Current status",
    "Next possible steps",
]

# Official optional headings (SPEC.md §5).
OPTIONAL_HEADINGS = [
    "Warnings",
    "Who this helps",
    "Simple analogy",
]

# Aliases that map mixed notes onto official headings. Keys are normalized.
_ALIASES: dict[str, str] = {
    "purpose": "Purpose",
    "why": "Purpose",
    "goal": "Purpose",
    "the purpose": "Purpose",
    "how it works": "How it works (plain English)",
    "how it works plain english": "How it works (plain English)",
    "how it works (plain english)": "How it works (plain English)",
    "walkthrough": "How it works (plain English)",
    "explanation": "How it works (plain English)",
    "how this works": "How it works (plain English)",
    "key ideas": "Key ideas",
    "key idea": "Key ideas",
    "concepts": "Key ideas",
    "key concepts": "Key ideas",
    "ideas": "Key ideas",
    "the actual code": "The actual code",
    "actual code": "The actual code",
    "code": "The actual code",
    "source": "The actual code",
    "the code": "The actual code",
    "original code": "The actual code",
    "line-by-line translation": "Line-by-line translation",
    "line-by-line": "Line-by-line translation",
    "line by line translation": "Line-by-line translation",
    "line by line": "Line-by-line translation",
    "translation": "Line-by-line translation",
    "decisions the program makes": "Decisions the program makes",
    "decisions": "Decisions the program makes",
    "branching": "Decisions the program makes",
    "what the program decides": "Decisions the program makes",
    "what a person would notice": "What a person would notice",
    "impact": "What a person would notice",
    "what you would notice": "What a person would notice",
    "what you'd notice": "What a person would notice",
    "what a person notices": "What a person would notice",
    "current status": "Current status",
    "status": "Current status",
    "next possible steps": "Next possible steps",
    "next steps": "Next possible steps",
    "future": "Next possible steps",
    "next": "Next possible steps",
    "warnings": "Warnings",
    "warning": "Warnings",
    "who this helps": "Who this helps",
    "audience": "Who this helps",
    "simple analogy": "Simple analogy",
    "analogy": "Simple analogy",
}

PLACEHOLDERS = {
    "Purpose": "This draft still needs a short everyday explanation of what the code is trying to achieve.",
    "How it works (plain English)": "This draft still needs a step-by-step description written in ordinary words.",
    "Key ideas": "- (key ideas still need to be named in everyday language)",
    "Line-by-line translation": "1. (each important line still needs a plain-English translation)",
    "Decisions the program makes": "- (the decisions this program makes still need to be listed in everyday words)",
    "What a person would notice": "This draft still needs a short note about how this would show up for a real person.",
    "Current status": "Unfinished draft — needs review.",
    "Next possible steps": "- Add the missing explanations so a non-programmer can follow the idea.",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LABEL_RE = re.compile(r"^([A-Za-z][A-Za-z 0-9()'/-]{0,60})\s*:\s*(.*)$")


@dataclass
class Change:
    kind: str
    message: str

    def line(self) -> str:
        return f"  [{self.kind}] {self.message}"


@dataclass
class TidyResult:
    source: str
    changes: list[Change] = field(default_factory=list)

    def report(self) -> str:
        lines = ["barrage-tidy report"]
        if not self.changes:
            lines.append("No changes.")
            lines.append("")
            return "\n".join(lines)
        lines.append(f"Found {len(self.changes)} change(s)/finding(s):")
        for change in self.changes:
            lines.append(change.line())
        lines.append("")
        return "\n".join(lines)


def _norm(title: str) -> str:
    cleaned = title.strip().lower()
    cleaned = cleaned.replace("’", "'")
    cleaned = re.sub(r"[#]+", "", cleaned)
    cleaned = re.sub(r"[._]+$", "", cleaned)
    cleaned = re.sub(r"[()]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _canonical_heading(title: str) -> str | None:
    return _ALIASES.get(_norm(title))


def _looks_like_code(text: str) -> bool:
    if "```" in text:
        return True
    clues = 0
    if re.search(r"[{};]", text):
        clues += 1
    if re.search(r"\b(if|for|while|def|function|return|var|let|const|class)\b", text):
        clues += 1
    if re.search(r"^\s{2,}\S", text, re.M):
        clues += 1
    return clues >= 2


def _fence_code(text: str) -> str:
    stripped = text.strip()
    if "```" in stripped:
        return stripped
    return "```\n" + stripped + "\n```"


def _todo(reason: str, leftover: str) -> str:
    # Markdown/HTML comment, the comment syntax Barrage inherits.
    body = leftover.strip().replace("-->", "->")
    clipped = body if len(body) <= 200 else body[:197] + "..."
    return f"<!-- BARRAGE-TODO: {reason} — {clipped} -->"



def _title_candidate(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or HEADING_RE.match(stripped) or stripped.startswith(">"):
        return None
    if LABEL_RE.match(stripped):
        return None
    if len(stripped) > 80 or "\n" in stripped:
        return None
    # A short heading-like first line, not a full prose sentence with a period mid-line.
    if stripped.endswith(".") and len(stripped.split()) > 8:
        return None
    if _looks_like_code(stripped):
        return None
    return stripped


def tidy(source: str) -> TidyResult:
    changes: list[Change] = []
    lines = source.splitlines()

    title: str | None = None
    # A first short line without a # heading often is the title in rough notes.
    stripped_lines = list(lines)
    while stripped_lines and not stripped_lines[0].strip():
        stripped_lines.pop(0)
    if stripped_lines:
        candidate = _title_candidate(stripped_lines[0])
        if candidate:
            title = candidate
            stripped_lines = stripped_lines[1:]
            lines = stripped_lines
    summary: str | None = None
    sections: dict[str, list[str]] = {}
    leftovers: list[tuple[str, str]] = []  # reason, text
    preamble: list[str] = []
    current: str | None = None  # None = preamble, or a canonical heading

    def flush_preamble() -> None:
        nonlocal preamble
        text = "\n".join(preamble).strip()
        preamble = []
        if not text:
            return
        if _looks_like_code(text) and "The actual code" not in sections:
            sections["The actual code"] = [_fence_code(text)]
            changes.append(Change("code", "Moved unmarked code into `## The actual code`"))
            return
        if "Purpose" not in sections:
            sections["Purpose"] = [text]
            changes.append(Change("section", "Used opening prose as `## Purpose`"))
            return
        leftovers.append(("could not place this leftover prose in an official section", text))

    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        heading = HEADING_RE.match(stripped)
        if heading:
            flush_preamble()
            level, name = heading.group(1), heading.group(2).strip()
            if level == "#" and title is None and _canonical_heading(name) is None:
                title = name
                current = None
                changes.append(Change("title", f"Kept title {title!r}"))
                i += 1
                continue
            canonical = _canonical_heading(name)
            if canonical:
                current = canonical
                sections.setdefault(canonical, [])
                if canonical != name:
                    changes.append(
                        Change("heading", f"Normalized heading {name!r} to official `{canonical}`")
                    )
                i += 1
                continue
            leftovers.append(
                (f"unknown heading {name!r} is not in the Barrage spec", stripped)
            )
            current = None
            i += 1
            continue

        # A line that is only an official heading name (or alias), without #.
        if stripped and not LABEL_RE.match(stripped) and len(stripped) <= 60:
            bare = _canonical_heading(stripped)
            if bare and _norm(stripped) in _ALIASES:
                flush_preamble()
                current = bare
                sections.setdefault(bare, [])
                if bare != stripped:
                    changes.append(
                        Change("heading", f"Normalized heading {stripped!r} to official `{bare}`")
                    )
                i += 1
                continue

        if stripped.startswith(">") and summary is None and current is None:
            summary = stripped[1:].strip()
            i += 1
            continue

        label = LABEL_RE.match(stripped)
        if label:
            canonical = _canonical_heading(label.group(1))
            if canonical:
                flush_preamble()
                body = label.group(2).strip()
                sections.setdefault(canonical, [])
                if body:
                    sections[canonical].append(body)
                changes.append(
                    Change("label", f"Mapped `{label.group(1)}:` to official `## {canonical}`")
                )
                current = canonical
                i += 1
                continue

        if current:
            sections.setdefault(current, []).append(raw)
        else:
            preamble.append(raw)
        i += 1

    flush_preamble()

    if title is None:
        title = "Untitled draft"
        changes.append(Change("title", "Added a placeholder title `# Untitled draft`"))
    if summary is None:
        summary = "This Barrage document still needs a one-sentence summary written for anyone."
        changes.append(Change("summary", "Added a placeholder one-sentence summary"))

    if "The actual code" in sections:
        body = "\n".join(sections["The actual code"]).strip()
        if "```" not in body:
            sections["The actual code"] = [_fence_code(body or "// (no code was found in the notes)")]
            changes.append(Change("code", "Wrapped the code section in a fenced block"))
    else:
        sections["The actual code"] = ["```\n// (no code was found in the notes)\n```"]
        changes.append(Change("code", "Added an empty fenced code block so the document meets the spec"))

    parts: list[str] = [f"# {title}", "", f"> {summary}", ""]
    for heading in REQUIRED_HEADINGS:
        parts.append(f"## {heading}")
        body = "\n".join(sections.get(heading, [])).strip()
        if not body:
            body = PLACEHOLDERS[heading]
            changes.append(Change("placeholder", f"Filled missing `{heading}` with a placeholder"))
        parts.append(body)
        parts.append("")

    for heading in OPTIONAL_HEADINGS:
        if heading in sections and any(line.strip() for line in sections[heading]):
            parts.append(f"## {heading}")
            parts.append("\n".join(sections[heading]).strip())
            parts.append("")

    for reason, text in leftovers:
        parts.append(_todo(reason, text))
        changes.append(Change("todo", f"Left unfixable text as an HTML comment ({reason})"))
        parts.append("")

    # Drop a "Kept title" change when the title was already present and we only recorded it.
    # Keep the report focused on real edits, but a keep is still useful? Drop noise.
    useful = []
    for change in changes:
        if change.kind == "title" and change.message.startswith("Kept title"):
            continue
        useful.append(change)
    changes = useful

    document = "\n".join(parts).rstrip() + "\n"
    errors = check_text(document)
    if errors:
        changes.append(
            Change("check", "Official structure check still reported: " + "; ".join(errors))
        )
    else:
        changes.append(Change("check", "Output matches the official Barrage required structure"))
    return TidyResult(source=document, changes=changes)

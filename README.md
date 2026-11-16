# barrage-tidy

Turn rough, mixed-style notes into a valid [Barrage](https://github.com/fitzyracing1/barrage) document.

Barrage is a plain-language markup format (not a programming language). A valid document wraps real code with official sections so a non-programmer can follow the idea. This helper is **rule-based** (no AI, no extra dependencies, offline). It normalizes notes onto the official headings from [SPEC.md](https://github.com/fitzyracing1/barrage/blob/main/SPEC.md) v1.0, fills any missing required section with a clearly marked placeholder, and leaves unfixable leftover lines as HTML comments (`<!-- BARRAGE-TODO: … -->`) — the comment form Barrage inherits from its Markdown-like structure. Nothing in the Barrage language is invented here.

The output is checked with a vendored copy of the official [barrage-checker](https://github.com/fitzyracing1/barrage-checker) rules. The Barrage language repository itself is not modified by this project.

Sponsor: [github.com/sponsors/fitzyracing1](https://github.com/sponsors/fitzyracing1).

## Install

```bash
pipx install git+https://github.com/fitzyracing1/barrage-tidy
```

Or from a checkout:

```bash
pip install -e .
```

## Usage

Print a tidied `.barrage` document on stdout (the change report goes to stderr):

```bash
barrage-tidy notes.barrage
python -m barrage_tidy notes.md
```

Write a new file named `notes.tidy.barrage` (the original is never overwritten):

```bash
barrage-tidy --write notes.barrage
```

The process exits `1` if the official structure check still fails, and `0` when the result is a valid Barrage document.

## What it does

- Recognizes official headings and common informal aliases (`purpose:`, `How it works`, `code:`, `status:`, and so on) and rewrites them to the exact SPEC.md names, in the required order.
- Keeps or adds `# Title` and a one-sentence `> summary`.
- Moves unmarked code into `## The actual code` inside a fenced block.
- Adds a short placeholder when a required section is missing, so the document can be checked.
- Leaves lines it cannot place as `<!-- BARRAGE-TODO: reason — … -->`.
- Validates the result against the official required sections, the required code fence, and the minimum length check.

Required sections (in order) are: Title, one-sentence summary, Purpose, How it works (plain English), Key ideas, The actual code, Line-by-line translation, Decisions the program makes, What a person would notice, Current status, Next possible steps. Optional official sections (Warnings, Who this helps, Simple analogy) are kept when present.

## License

MIT. Copyright (c) 2026 Joshua Almeida (fitzyracing1).

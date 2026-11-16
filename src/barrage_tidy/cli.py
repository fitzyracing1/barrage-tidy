"""Command-line interface for barrage-tidy."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from barrage_tidy import __version__
from barrage_tidy.checker import check_text
from barrage_tidy.tidy import tidy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="barrage-tidy",
        description=(
            "Turn rough, mixed-style notes into a valid Barrage document "
            "(plain-language markup from fitzyracing1/barrage). Prints a "
            "change report on stderr. Never overwrites the input file."
        ),
    )
    parser.add_argument(
        "file",
        help="Path to a .barrage / .brg / .md file, or any text file of rough notes",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write tidied source to FILE.tidy.barrage (never overwrites FILE)",
    )
    parser.add_argument("--version", action="version", version=f"barrage-tidy {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = Path(args.file)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as err:
        print(f"barrage-tidy: cannot read {path}: {err}", file=sys.stderr)
        return 1

    result = tidy(source)
    sys.stderr.write(result.report())
    errors = check_text(result.source)
    if errors:
        sys.stderr.write("Official structure check still reported:\n")
        for item in errors:
            sys.stderr.write(f"  - {item}\n")

    if args.write:
        dest = path.with_name(path.stem + ".tidy.barrage")
        dest.write_text(result.source, encoding="utf-8")
        sys.stderr.write(f"Wrote {dest}\n")
    else:
        sys.stdout.write(result.source)
        if result.source and not result.source.endswith("\n"):
            sys.stdout.write("\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Approximate word count for the Paper Track draft (≤ 3000)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "paper" / "DRAFT.md"
LIMIT = 3000


def strip_for_count(md: str) -> str:
    # Drop HTML comments (budgets, TODOs, status)
    md = re.sub(r"<!--.*?-->", " ", md, flags=re.S)
    # Fenced code blocks (figure ASCII, etc.) — still "words" on Kaggle? count conservatively OUT
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    # Links: keep link text
    md = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", md)
    # Markdown chrome
    md = re.sub(r"[#>*`|_\[\]()]", " ", md)
    md = re.sub(r"\$\$[^$]+\$\$", " ", md)
    md = re.sub(r"\$[^$]+\$", " ", md)
    return md


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT)
    args = parser.parse_args()
    text = args.path.read_text(encoding="utf-8")
    words = strip_for_count(text).split()
    n = len(words)
    remaining = LIMIT - n
    status = "OK" if n <= LIMIT else "OVER LIMIT"
    print(f"{args.path}: {n} words ({status}; {remaining:+d} vs {LIMIT})")


if __name__ == "__main__":
    main()

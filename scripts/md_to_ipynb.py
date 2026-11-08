#!/usr/bin/env python3
"""Convert notebooks/*.md scaffold (## sections + fenced code) into .ipynb."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def convert(md_path: Path, out_path: Path) -> int:
    lines = md_path.read_text(encoding="utf-8").splitlines(keepends=True)
    blocks: list[tuple[str, str]] = []
    buf_md: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```") and stripped != "```":
            if buf_md:
                blocks.append(("markdown", "".join(buf_md).strip()))
                buf_md = []
            lang = stripped[3:]
            i += 1
            code: list[str] = []
            while i < len(lines) and lines[i].strip() != "```":
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            body = "".join(code).rstrip() + "\n"
            if lang == "python":
                blocks.append(("code", body))
            else:
                blocks.append(("markdown", f"```{lang}\n{body}```"))
            continue
        buf_md.append(line)
        i += 1
    if buf_md:
        blocks.append(("markdown", "".join(buf_md).strip()))

    cells = []
    for typ, src in blocks:
        if not src.strip():
            continue
        if typ == "code":
            cells.append(
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": src.splitlines(keepends=True),
                }
            )
        else:
            cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": (src + "\n").splitlines(keepends=True),
                }
            )

    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": cells,
    }
    out_path.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
    return len(cells)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    md = root / "notebooks" / "moepa-graph-walkthrough.md"
    out = root / "notebooks" / "moepa-graph-walkthrough.ipynb"
    n = convert(md, out)
    print(f"wrote {out} ({n} cells)")


if __name__ == "__main__":
    main()
    sys.exit(0)

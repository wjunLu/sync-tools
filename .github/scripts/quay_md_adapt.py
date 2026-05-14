#!/usr/bin/env python3
"""Adapt markdown for quay.io's repository description renderer.

quay.io's Information tab uses react-markdown, but the deployed build does not
render GFM pipe tables — they collapse onto one line as literal text. Inline
HTML <table> tags are also stripped because rehype-raw is not enabled. The only
form that renders reliably is a plain bullet list, so we rewrite each pipe
table to "*<header line>*" followed by one bullet per row.

Usage: quay_md_adapt.py <input.md> <output.md>
"""
import re
import sys
import pathlib


def parse_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def is_separator(line: str) -> bool:
    s = line.strip()
    if not s.startswith("|"):
        return False
    cells = [c for c in parse_row(s) if c]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def render_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    headers = [h for h in headers if h]
    if not headers:
        return []
    out = ["*" + " — ".join(headers) + "*", ""]
    for row in rows:
        cells = (row + [""] * len(headers))[: len(headers)]
        if not any(cells):
            continue
        first, rest = cells[0], [c for c in cells[1:] if c]
        line = f"- **{first}**" if first else "-"
        if rest:
            line += " — " + " — ".join(rest)
        out.append(line)
    out.append("")
    return out


def convert(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if (
            i + 1 < len(lines)
            and lines[i].lstrip().startswith("|")
            and is_separator(lines[i + 1])
        ):
            headers = parse_row(lines[i])
            j = i + 2
            rows: list[list[str]] = []
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(parse_row(lines[j]))
                j += 1
            out.extend(render_table(headers, rows))
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: quay_md_adapt.py <input.md> <output.md>", file=sys.stderr)
        sys.exit(2)
    src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    pathlib.Path(sys.argv[2]).write_text(convert(src), encoding="utf-8")


if __name__ == "__main__":
    main()

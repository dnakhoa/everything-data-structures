#!/usr/bin/env python3
"""Book integrity checks. Run from the repo root: python3 scripts/check_book.py

1. Every Python code block parses.
2. Every link in SUMMARY.md resolves to a file that exists.
3. Every chapter page starts with a single H1.
4. Code fences are balanced.
5. SVG files contain no blank lines (a blank line ends the raw-HTML block in Markdown).
"""
import ast
import glob
import os
import re
import sys

SRC = "src"
FENCE = re.compile(r"^```(\w*)\s*$")
CLOSE = re.compile(r"^```\s*$")

errors = []


def fail(msg):
    errors.append(msg)


def iter_md():
    return sorted(glob.glob(os.path.join(SRC, "**", "*.md"), recursive=True))


def check_python_blocks():
    checked = 0
    for path in iter_md():
        lines = open(path, encoding="utf-8").read().split("\n")
        lang, buf, start = None, [], 0
        for i, ln in enumerate(lines):
            m = FENCE.match(ln)
            if m and lang is None:
                lang, buf, start = m.group(1), [], i + 1
                continue
            if CLOSE.match(ln) and lang is not None:
                if lang == "python":
                    checked += 1
                    try:
                        ast.parse("\n".join(buf))
                    except SyntaxError as e:
                        fail("%s:%d python block does not parse: %s" % (path, start, e.msg))
                lang = None
                continue
            if lang is not None:
                buf.append(ln)
        if lang is not None:
            fail("%s: unbalanced code fence (opened at line %d, never closed)" % (path, start))
    print("  %d python blocks parsed" % checked)


def check_summary_links():
    summary = os.path.join(SRC, "SUMMARY.md")
    text = open(summary, encoding="utf-8").read()
    targets = re.findall(r"\]\(([^)]+)\)", text)
    for t in targets:
        if not t or t.startswith("http"):
            continue
        full = os.path.join(SRC, t.split("#")[0])
        if not os.path.exists(full):
            fail("SUMMARY.md links to a missing file: %s" % t)
    print("  %d SUMMARY links checked" % len(targets))


def check_headings():
    for path in iter_md():
        if path.endswith("SUMMARY.md"):
            continue
        first = open(path, encoding="utf-8").readline().rstrip("\n")
        if not first.startswith("# "):
            fail("%s: first line is not an H1 (found %r)" % (path, first[:40]))
    print("  headings checked")


def check_internal_links():
    """Relative markdown links inside chapters must resolve."""
    count = 0
    for path in iter_md():
        text = open(path, encoding="utf-8").read()
        for target in re.findall(r"\]\((?!http)([^)#\s]+\.md)[^)]*\)", text):
            count += 1
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                fail("%s: broken link to %s" % (path, target))
    print("  %d internal links checked" % count)


def check_svgs():
    for path in sorted(glob.glob(os.path.join(SRC, "images", "*.svg"))):
        content = open(path, encoding="utf-8").read()
        if re.search(r"\n[ \t]*\n", content):
            fail("%s: contains a blank line — this breaks inline embedding in Markdown" % path)
        if "currentColor" not in content:
            fail("%s: no currentColor — the diagram will not adapt to the dark theme" % path)
    print("  svgs checked")


if __name__ == "__main__":
    print("Checking book integrity...")
    check_python_blocks()
    check_summary_links()
    check_headings()
    check_internal_links()
    check_svgs()

    if errors:
        print("\n%d problem(s) found:\n" % len(errors))
        for e in errors:
            print("  ✗ %s" % e)
        sys.exit(1)
    print("\nAll checks passed.")

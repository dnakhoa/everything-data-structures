#!/usr/bin/env python3
"""Book integrity checks. Run from the repo root: python3 scripts/check_book.py

1. Every Python code block parses.
2. Every link in SUMMARY.md resolves to a file that exists.
3. Every chapter page starts with a single H1.
4. Code fences are balanced.
5. SVG files contain no blank lines (a blank line ends the raw-HTML block in Markdown).
   Figures included on the same page must not define the same CSS class or element id,
   because inline <style> rules apply to the whole page.
6. Every chapter has an Exercises section, numbered for that chapter, and every
   <details> hint/solution block is balanced and padded with the blank lines
   mdBook needs to render the Markdown inside it.
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
    # Inline SVG styles and ids are page-global: two figures on one page must not
    # share a class name or an id, or one restyles (or re-targets) the other.
    for page in iter_md():
        figs = re.findall(r"\{\{#include \.\./images/([\w-]+\.svg)\}\}", open(page, encoding="utf-8").read())
        seen_cls, seen_id = {}, {}
        for f in figs:
            content = open(os.path.join(SRC, "images", f), encoding="utf-8").read()
            style = re.search(r"<style>(.*?)</style>", content, re.S)
            for cls in set(re.findall(r"\.([A-Za-z_][\w-]*)", style.group(1) if style else "")):
                if cls in seen_cls and seen_cls[cls] != f:
                    fail("%s: figures %s and %s both define CSS class .%s (prefix classes with the file name)" % (page, seen_cls[cls], f, cls))
                seen_cls.setdefault(cls, f)
            for i in set(re.findall(r'\bid="([^"]+)"', content)):
                if i in seen_id and seen_id[i] != f:
                    fail("%s: figures %s and %s both use id=%s" % (page, seen_id[i], f, i))
                seen_id.setdefault(i, f)
    print("  svgs checked")


def check_exercises():
    chapters = [p for p in iter_md() if re.match(r"ch\d+-", os.path.basename(p))]
    total = 0
    for path in chapters:
        num = int(re.match(r"ch(\d+)-", os.path.basename(path)).group(1))
        lines = open(path, encoding="utf-8").read().split("\n")
        if "## Exercises" not in lines:
            fail("%s: no '## Exercises' section" % path)
            continue
        found = re.findall(r"^\*\*(\d+)\.(\d+) ", "\n".join(lines), re.M)
        if not found:
            fail("%s: Exercises section has no numbered exercises" % path)
        for ch, n in found:
            if int(ch) != num:
                fail("%s: exercise %s.%s is misnumbered (chapter %d)" % (path, ch, n, num))
        nums = [int(n) for _, n in found]
        if nums != list(range(1, len(nums) + 1)):
            fail("%s: exercises are not numbered 1..%d in order" % (path, len(nums)))
        total += len(found)

        depth, in_code = 0, False
        for i, ln in enumerate(lines):
            if ln.lstrip().startswith("```"):
                in_code = not in_code
            if in_code:
                continue
            s = ln.strip()
            if s == "<details>":
                depth += 1
                if depth > 1:
                    fail("%s:%d nested <details>" % (path, i + 1))
            elif s == "</details>":
                depth -= 1
                if depth < 0:
                    fail("%s:%d </details> without <details>" % (path, i + 1))
                if i > 0 and lines[i - 1].strip():
                    fail("%s:%d needs a blank line before </details>" % (path, i + 1))
            elif s.startswith("<summary>"):
                if i + 1 < len(lines) and lines[i + 1].strip():
                    fail("%s:%d needs a blank line after <summary>" % (path, i + 1))
        if depth != 0:
            fail("%s: unbalanced <details> blocks" % path)
    print("  %d exercises in %d chapters checked" % (total, len(chapters)))


if __name__ == "__main__":
    print("Checking book integrity...")
    check_python_blocks()
    check_summary_links()
    check_headings()
    check_internal_links()
    check_svgs()
    check_exercises()

    if errors:
        print("\n%d problem(s) found:\n" % len(errors))
        for e in errors:
            print("  ✗ %s" % e)
        sys.exit(1)
    print("\nAll checks passed.")

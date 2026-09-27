"""Programmatic checks for the eval runs: PDF page count and response language.

Usage: python3 auto_checks.py <iteration-dir>
Prints JSON {run_dir: {"pdf_pages": n|None, "ukrainian": bool, "response_chars": n}}.
"""
import json
import re
import sys
from pathlib import Path


def pdf_pages(path: Path):
    if not path.exists():
        return None
    data = path.read_bytes()
    m = re.findall(rb"/Type\s*/Pages\b.*?/Count\s+(\d+)", data, flags=re.S)
    if m:
        return max(int(x) for x in m)
    return len(re.findall(rb"/Type\s*/Page(?!s)", data))


def ukrainian(text: str) -> bool:
    letters = re.findall(r"[A-Za-zА-Яа-яІіЇїЄєҐґ]", text)
    cyr = [c for c in letters if re.match(r"[А-Яа-яІіЇїЄєҐґ]", c)]
    uk_specific = len(re.findall(r"[ІіЇїЄєҐґ]", text))
    return bool(letters) and len(cyr) / len(letters) > 0.6 and uk_specific > 5


def main(root: str):
    out = {}
    for run in sorted(Path(root).glob("*/*/outputs")):
        resp = run / "response.md"
        text = resp.read_text(encoding="utf-8") if resp.exists() else ""
        out[str(run.parent.relative_to(root))] = {
            "pdf_pages": pdf_pages(run / "report.pdf"),
            "ukrainian": ukrainian(text),
            "response_chars": len(text),
        }
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])

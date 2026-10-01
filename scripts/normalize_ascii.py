"""Normalize LLM-typical Unicode punctuation to ASCII (fleet hygiene gate).

Replaces em/en dashes, smart quotes, and mojibake markers with ASCII
equivalents. Run: uv run python scripts/normalize_ascii.py [paths...]
Defaults to intentional source trees (docs, prompts, skills, webapp src).
"""

import sys
from pathlib import Path

REPLACEMENTS = {
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "\u2018": "'",  # left single quote
    "\u2019": "'",  # right single quote
    "\u201c": '"',  # left double quote
    "\u201d": '"',  # right double quote
    "\ufffd": "-",  # mojibake replacement char
}

DEFAULT_ROOTS = ["docs", "mcpb/assets/prompts", "src", "webapp/src", "README.md",
                 "INSTALL.md", "AGENTS.md", "CLAUDE.md", "CHANGELOG.md", "HANDOVER.md"]
EXTS = {".md", ".py", ".tsx", ".ts"}


def normalize_file(path: Path) -> int:
    # newline="": never let Windows text-mode translation sneak CRLF in.
    with path.open("r", encoding="utf-8", newline="") as f:
        text = f.read()
    count = 0
    for bad, good in REPLACEMENTS.items():
        n = text.count(bad)
        if n:
            text = text.replace(bad, good)
            count += n
    if count:
        with path.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return count


def main(argv: list[str]) -> int:
    repo = Path(__file__).parent.parent
    targets = argv[1:] or DEFAULT_ROOTS
    total = 0
    files = 0
    for t in targets:
        p = repo / t
        if p.is_file():
            candidates = [p]
        else:
            candidates = [f for f in p.rglob("*") if f.suffix in EXTS
                          and "node_modules" not in f.parts and ".venv" not in f.parts]
        for f in candidates:
            n = normalize_file(f)
            if n:
                print(f"{f.relative_to(repo)}: {n} replaced")
                files += 1
                total += n
    print(f"done: {total} replacements in {files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

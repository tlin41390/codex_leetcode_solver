from __future__ import annotations

from pathlib import Path
from urllib import request


def fetch_url_text(url: str) -> str:
    req = request.Request(
        url=url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; leetcode-solver/0.1)"},
        method="GET",
    )
    with request.urlopen(req, timeout=30.0) as response:
        return response.read().decode("utf-8", errors="replace")


def load_problem_text(file_path: str | None, url: str | None, stdin_fallback: bool = True) -> str:
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Problem file not found: {path}")
        content = path.read_text(encoding="utf-8").strip()
    elif url:
        content = fetch_url_text(url).strip()
    elif stdin_fallback:
        print("Paste the full LeetCode problem description. End input with Ctrl+Z then Enter (Windows).")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        content = "\n".join(lines).strip()
    else:
        content = ""

    if not content:
        raise ValueError("No problem description provided")

    return content

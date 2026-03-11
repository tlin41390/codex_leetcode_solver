from __future__ import annotations

import argparse
import json
from pathlib import Path

from .env_utils import load_dotenv_file
from .input_loader import load_problem_text
from .llm_client import OpenAICompatibleClient
from .solver import LeetCodeSolver


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LeetCode multi-language solver with algorithm explanation")
    parser.add_argument("--file", help="Path to a text/markdown file with the LeetCode problem description")
    parser.add_argument("--url", help="Optional URL containing the problem description (e.g. LeetCode page)")
    parser.add_argument(
        "--languages",
        default="python,java,javascript",
        help="Comma-separated target languages (e.g. python,java,cpp)",
    )
    parser.add_argument("--model", default="gpt-4.1", help="Model name for the OpenAI-compatible endpoint")
    parser.add_argument("--base-url", default=None, help="Optional OpenAI-compatible base URL")
    parser.add_argument("--output", default=None, help="Optional output JSON file path")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format",
    )
    return parser.parse_args()


def to_markdown(result: dict) -> str:
    lines = [
        f"# {result['title']}",
        "",
        "## Problem Summary",
        result["problem_summary"],
        "",
        "## Algorithm",
        result["algorithm"],
        "",
        "## Complexity",
        f"- Time: `{result['time_complexity']}`",
        f"- Space: `{result['space_complexity']}`",
        "",
        "## Edge Cases",
    ]

    if result.get("edge_cases"):
        lines.extend([f"- {item}" for item in result["edge_cases"]])
    else:
        lines.append("- None provided")

    lines.append("")
    lines.append("## Code Solutions")
    for solution in result["solutions"]:
        lang = solution["language"]
        lines.extend([
            "",
            f"### {lang}",
            f"```{lang.lower()}",
            solution["code"],
            "```",
        ])

    lines.append("")
    lines.append("## Related Problems")
    related = result.get("related_problems") or []
    if related:
        for item in related:
            title = item.get("title", "Unknown")
            difficulty = item.get("difficulty", "Unknown")
            url = item.get("url", "")
            reason = item.get("reason", "")
            if url:
                lines.append(f"- [{title}]({url}) ({difficulty}) - {reason}")
            else:
                lines.append(f"- {title} ({difficulty}) - {reason}")
    else:
        lines.append("- None provided")

    return "\n".join(lines)


def main() -> None:
    load_dotenv_file()
    args = parse_args()

    languages = [x.strip() for x in args.languages.split(",") if x.strip()]
    problem_text = load_problem_text(args.file, args.url)

    client = OpenAICompatibleClient.from_env(model=args.model, base_url=args.base_url)
    solver = LeetCodeSolver(client)
    result = solver.solve(problem_text=problem_text, languages=languages)
    payload = result.to_dict()

    output_text = json.dumps(payload, indent=2) if args.format == "json" else to_markdown(payload)

    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
        print(f"Wrote output to {args.output}")
    else:
        print(output_text)


if __name__ == "__main__":
    main()

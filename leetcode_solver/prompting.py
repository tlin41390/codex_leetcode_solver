from __future__ import annotations

from typing import Iterable


def build_prompt(problem_text: str, languages: Iterable[str]) -> str:
    langs = ", ".join(languages)
    return f"""
You are an expert competitive programming assistant.
Given the LeetCode problem description, generate a correct and efficient solution.

Requirements:
1) Return valid JSON only (no markdown fences, no extra text).
2) Follow this exact JSON structure:
{{
  "title": "string",
  "problem_summary": "string",
  "algorithm": "string",
  "data_structure_algorithm": ["string", "..."],
  "time_complexity": "string",
  "space_complexity": "string",
  "edge_cases": ["string", "..."],
  "solutions": [
    {{"language": "string", "code": "string"}}
  ],
  "related_problems": [
    {{
      "title": "string",
      "difficulty": "Easy|Medium|Hard",
      "url": "string",
      "reason": "string"
    }}
  ]
}}
3) Generate one solution for each requested language: {langs}
4) Solutions must be complete and runnable with idiomatic style for each language.
5) The algorithm explanation should be detailed and practical.
6) Complexity must match the provided implementation.
7) Provide 3 to 5 related LeetCode problems for practice. If exact URLs are unknown, still provide best-effort titles and reasons.
8) Fill "data_structure_algorithm" with a concise list of categories used by this solution (for example: Hash Map, Two Pointers, Binary Search, Dynamic Programming, Graph Traversal, Sliding Window, Heap).

LeetCode Problem Description:
{problem_text}
""".strip()

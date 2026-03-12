from __future__ import annotations

import unittest

from leetcode_solver.llm_client import compute_retry_delay, extract_json
from leetcode_solver.models import SolverOutput


class ParsingTests(unittest.TestCase):
    def test_extract_json_from_plain_text(self) -> None:
        payload = extract_json('{"title":"t","problem_summary":"s","algorithm":"a","time_complexity":"O(n)","space_complexity":"O(n)","edge_cases":[],"solutions":[{"language":"python","code":"print(1)"}]}')
        self.assertEqual(payload["title"], "t")

    def test_extract_json_from_fenced_block(self) -> None:
        raw = "```json\n{\"title\":\"t\",\"problem_summary\":\"s\",\"algorithm\":\"a\",\"time_complexity\":\"O(n)\",\"space_complexity\":\"O(n)\",\"edge_cases\":[],\"solutions\":[{\"language\":\"python\",\"code\":\"print(1)\"}]}\n```"
        payload = extract_json(raw)
        self.assertEqual(payload["solutions"][0]["language"], "python")

    def test_schema_validation(self) -> None:
        data = {
            "title": "Two Sum",
            "problem_summary": "Find two indices.",
            "algorithm": "Use hash map.",
            "data_structure_algorithm": ["Hash Map"],
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
            "edge_cases": ["duplicates"],
            "solutions": [{"language": "python", "code": "pass"}],
            "related_problems": [
                {
                    "title": "Contains Duplicate",
                    "difficulty": "Easy",
                    "url": "https://leetcode.com/problems/contains-duplicate/",
                    "reason": "Also uses hash-based lookup patterns.",
                }
            ],
        }
        obj = SolverOutput.from_dict(data)
        self.assertEqual(obj.time_complexity, "O(n)")
        self.assertEqual(obj.data_structure_algorithm, ["Hash Map"])
        self.assertEqual(obj.related_problems[0].difficulty, "Easy")

    def test_retry_delay_uses_retry_after(self) -> None:
        self.assertEqual(compute_retry_delay(2, "3"), 3.0)

    def test_retry_delay_fallback_exponential(self) -> None:
        self.assertEqual(compute_retry_delay(0, None), 1.0)
        self.assertEqual(compute_retry_delay(3, None), 8.0)


if __name__ == "__main__":
    unittest.main()

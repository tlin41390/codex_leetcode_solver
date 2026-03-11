from __future__ import annotations

import unittest

from leetcode_solver.webapp import parse_languages


class WebAppTests(unittest.TestCase):
    def test_parse_languages(self) -> None:
        self.assertEqual(parse_languages("python, java ,cpp"), ["python", "java", "cpp"])

    def test_parse_languages_empty(self) -> None:
        with self.assertRaises(ValueError):
            parse_languages("  , ")


if __name__ == "__main__":
    unittest.main()

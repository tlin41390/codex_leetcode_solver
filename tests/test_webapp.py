from __future__ import annotations

import unittest

from leetcode_solver.webapp import SessionStore, parse_languages


class WebAppTests(unittest.TestCase):
    def test_parse_languages(self) -> None:
        self.assertEqual(parse_languages("python, java ,cpp"), ["python", "java", "cpp"])

    def test_parse_languages_empty(self) -> None:
        with self.assertRaises(ValueError):
            parse_languages("  , ")

    def test_delete_session_removes_data(self) -> None:
        store = SessionStore()
        first = store.create_session("First")
        second = store.create_session("Second")
        store.add_item(
            session=first,
            problem_text="two sum",
            languages=["python"],
            result={"title": "Two Sum"},
        )

        deleted = store.delete_session(first["session_id"])

        self.assertEqual(deleted["session_id"], first["session_id"])
        self.assertIsNone(store.get_session(first["session_id"]))
        self.assertIsNotNone(store.get_session(second["session_id"]))

    def test_delete_only_session_fails(self) -> None:
        store = SessionStore()
        only = store.create_session("Only")
        with self.assertRaises(ValueError):
            store.delete_session(only["session_id"])

    def test_delete_unknown_session_fails(self) -> None:
        store = SessionStore()
        store.create_session("A")
        store.create_session("B")
        with self.assertRaises(KeyError):
            store.delete_session("missing")

    def test_session_name_updates_to_problem_title(self) -> None:
        store = SessionStore()
        session = store.create_session("Initial")
        store.add_item(
            session=session,
            problem_text="first problem",
            languages=["python"],
            result={"title": "Two Sum"},
        )
        self.assertEqual(session["name"], "Two Sum")
        self.assertEqual(session["latest_title"], "Two Sum")

        store.add_item(
            session=session,
            problem_text="different problem",
            languages=["python"],
            result={"title": "Valid Parentheses"},
        )
        self.assertEqual(session["name"], "Valid Parentheses")
        self.assertEqual(session["latest_title"], "Valid Parentheses")

    def test_duplicate_problem_titles_get_suffixes(self) -> None:
        store = SessionStore()
        first = store.create_session("S1")
        second = store.create_session("S2")
        third = store.create_session("S3")

        for session in (first, second, third):
            store.add_item(
                session=session,
                problem_text="same",
                languages=["python"],
                result={"title": "Two Sum"},
            )

        names = {first["name"], second["name"], third["name"]}
        self.assertEqual(names, {"Two Sum", "Two Sum (2)", "Two Sum (3)"})

    def test_new_empty_session_is_untitled(self) -> None:
        store = SessionStore()
        session = store.create_session()
        self.assertEqual(session["name"], "Untitled")
        self.assertEqual(session["latest_title"], "Untitled")

    def test_main_headline_is_used_for_session_name(self) -> None:
        store = SessionStore()
        session = store.create_session()
        store.add_item(
            session=session,
            problem_text="problem",
            languages=["python"],
            result={"title": "# 1. Two Sum\nDetails and notes"},
        )
        self.assertEqual(session["name"], "Two Sum")
        self.assertEqual(session["latest_title"], "Two Sum")


if __name__ == "__main__":
    unittest.main()

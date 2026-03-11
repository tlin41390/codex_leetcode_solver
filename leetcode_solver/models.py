from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, List


@dataclass
class LanguageSolution:
    language: str
    code: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LanguageSolution":
        language = str(data.get("language", "")).strip()
        code = str(data.get("code", "")).strip()
        if not language or not code:
            raise ValueError("Each solution must include non-empty language and code")
        return LanguageSolution(language=language, code=code)


@dataclass
class RelatedProblem:
    title: str
    difficulty: str
    url: str
    reason: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RelatedProblem":
        title = str(data.get("title", "")).strip()
        difficulty = str(data.get("difficulty", "")).strip()
        url = str(data.get("url", "")).strip()
        reason = str(data.get("reason", "")).strip()
        if not title:
            raise ValueError("Each related problem must include a title")
        return RelatedProblem(title=title, difficulty=difficulty, url=url, reason=reason)


@dataclass
class SolverOutput:
    title: str
    problem_summary: str
    algorithm: str
    time_complexity: str
    space_complexity: str
    edge_cases: List[str] = field(default_factory=list)
    solutions: List[LanguageSolution] = field(default_factory=list)
    related_problems: List[RelatedProblem] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SolverOutput":
        required = [
            "title",
            "problem_summary",
            "algorithm",
            "time_complexity",
            "space_complexity",
            "solutions",
        ]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        solutions_raw = data.get("solutions")
        if not isinstance(solutions_raw, list) or not solutions_raw:
            raise ValueError("At least one language solution must be generated")

        edge_cases_raw = data.get("edge_cases", [])
        if not isinstance(edge_cases_raw, list):
            raise ValueError("edge_cases must be a list of strings")
        edge_cases = [str(item) for item in edge_cases_raw]
        related_raw = data.get("related_problems", [])
        if not isinstance(related_raw, list):
            raise ValueError("related_problems must be a list")

        return SolverOutput(
            title=str(data["title"]).strip(),
            problem_summary=str(data["problem_summary"]).strip(),
            algorithm=str(data["algorithm"]).strip(),
            time_complexity=str(data["time_complexity"]).strip(),
            space_complexity=str(data["space_complexity"]).strip(),
            edge_cases=edge_cases,
            solutions=[LanguageSolution.from_dict(item) for item in solutions_raw],
            related_problems=[RelatedProblem.from_dict(item) for item in related_raw],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

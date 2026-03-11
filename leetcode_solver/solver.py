from __future__ import annotations

from typing import Iterable

from .llm_client import OpenAICompatibleClient, extract_json
from .models import SolverOutput
from .prompting import build_prompt


class LeetCodeSolver:
    def __init__(self, client: OpenAICompatibleClient):
        self.client = client

    def solve(self, problem_text: str, languages: Iterable[str]) -> SolverOutput:
        lang_list = [lang.strip() for lang in languages if lang.strip()]
        if not lang_list:
            raise ValueError("At least one target language is required")

        prompt = build_prompt(problem_text=problem_text, languages=lang_list)
        raw = self.client.complete(prompt)
        parsed = extract_json(raw)
        return SolverOutput.from_dict(parsed)

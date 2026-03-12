from __future__ import annotations

import argparse
import uuid
from pathlib import Path
from typing import Any

from .env_utils import load_dotenv_file
from .llm_client import OpenAICompatibleClient
from .solver import LeetCodeSolver


def parse_languages(raw: str) -> list[str]:
    langs = [item.strip() for item in raw.split(",") if item.strip()]
    if not langs:
        raise ValueError("At least one language is required")
    return langs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LeetCode Solver Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    parser.add_argument("--model", default="gpt-4.1", help="Model name for OpenAI-compatible endpoint")
    parser.add_argument("--base-url", default=None, help="Optional OpenAI-compatible base URL")
    return parser.parse_args()


class SessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}

    def session_summary(self, session: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": session["session_id"],
            "name": session["name"],
            "updated_at": session["updated_at"],
            "latest_title": session.get("latest_title", "Untitled"),
        }

    def create_session(self, name: str | None = None) -> dict[str, Any]:
        sid = str(uuid.uuid4())
        session = {
            "session_id": sid,
            "name": (name or f"Session {len(self.sessions) + 1}").strip(),
            "items": [],
            "updated_at": 0,
            "latest_title": "Untitled",
        }
        self.sessions[sid] = session
        return session

    def list_summaries(self) -> list[dict[str, Any]]:
        items = [self.session_summary(s) for s in self.sessions.values()]
        items.sort(key=lambda x: x["updated_at"], reverse=True)
        return items

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self.sessions.get(session_id)

    def add_item(self, session: dict[str, Any], problem_text: str, languages: list[str], result: dict[str, Any]) -> None:
        session["items"].append(
            {
                "problem_text": problem_text,
                "languages": languages,
                "result": result,
            }
        )
        session["updated_at"] += 1
        session["latest_title"] = result.get("title", "Untitled")


def create_app(model: str, base_url: str | None):
    try:
        from fastapi import Body, FastAPI, HTTPException
        from fastapi.responses import HTMLResponse, JSONResponse
    except ImportError as exc:
        raise RuntimeError("FastAPI is not installed. Install dependencies with: pip install -e .") from exc

    client = OpenAICompatibleClient.from_env(model=model, base_url=base_url)
    solver = LeetCodeSolver(client)
    html_path = Path(__file__).parent / "static" / "index.html"
    store = SessionStore()
    app = FastAPI(title="LeetCode Solver UI")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return html_path.read_text(encoding="utf-8")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/sessions")
    async def list_sessions() -> dict[str, Any]:
        return {"sessions": store.list_summaries()}

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str) -> dict[str, Any]:
        session = store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "session": store.session_summary(session),
            "items": session["items"],
        }

    @app.post("/api/sessions")
    async def create_session(body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        created = store.create_session(str(body.get("name", "")).strip() or None)
        return {"session": store.session_summary(created)}

    @app.post("/api/solve")
    async def solve(body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        problem_text = str(body.get("problem_text", "")).strip()
        if not problem_text:
            raise HTTPException(status_code=400, detail="problem_text is required")

        try:
            if isinstance(body.get("languages"), list):
                languages = [str(item).strip() for item in body["languages"] if str(item).strip()]
                if not languages:
                    raise ValueError("At least one language is required")
            else:
                languages = parse_languages(str(body.get("languages", "")))
            result = solver.solve(problem_text=problem_text, languages=languages).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Solve failed: {exc}") from exc

        session_id = str(body.get("session_id", "")).strip()
        session = store.get_session(session_id)
        if not session:
            session = store.create_session()

        store.add_item(session=session, problem_text=problem_text, languages=languages, result=result)
        return {
            "result": result,
            "session": store.session_summary(session),
        }

    return app


def main() -> None:
    load_dotenv_file()
    args = parse_args()
    app = create_app(model=args.model, base_url=args.base_url)
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("uvicorn is not installed. Install dependencies with: pip install -e .") from exc
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

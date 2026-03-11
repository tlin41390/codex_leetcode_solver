from __future__ import annotations

import argparse
import json
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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


def build_handler(model: str, base_url: str | None) -> type[BaseHTTPRequestHandler]:
    client = OpenAICompatibleClient.from_env(model=model, base_url=base_url)
    solver = LeetCodeSolver(client)
    html_path = Path(__file__).parent / "static" / "index.html"
    sessions: dict[str, dict[str, Any]] = {}

    def session_summary(session: dict[str, Any]) -> dict[str, Any]:
        return {
            "session_id": session["session_id"],
            "name": session["name"],
            "updated_at": session["updated_at"],
            "latest_title": session.get("latest_title", "Untitled"),
        }

    def create_session(name: str | None = None) -> dict[str, Any]:
        sid = str(uuid.uuid4())
        session = {
            "session_id": sid,
            "name": (name or f"Session {len(sessions) + 1}").strip(),
            "items": [],
            "updated_at": 0,
            "latest_title": "Untitled",
        }
        sessions[sid] = session
        return session

    class Handler(BaseHTTPRequestHandler):
        def _json_response(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _text_response(self, status: int, text: str, content_type: str) -> None:
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                html = html_path.read_text(encoding="utf-8")
                self._text_response(HTTPStatus.OK, html, "text/html; charset=utf-8")
                return
            if parsed.path == "/health":
                self._json_response(HTTPStatus.OK, {"status": "ok"})
                return
            if parsed.path == "/api/sessions":
                items = [session_summary(s) for s in sessions.values()]
                items.sort(key=lambda x: x["updated_at"], reverse=True)
                self._json_response(HTTPStatus.OK, {"sessions": items})
                return
            if parsed.path.startswith("/api/sessions/"):
                session_id = parsed.path.replace("/api/sessions/", "", 1).strip()
                session = sessions.get(session_id)
                if not session:
                    self._json_response(HTTPStatus.NOT_FOUND, {"error": "Session not found"})
                    return
                self._json_response(
                    HTTPStatus.OK,
                    {
                        "session": session_summary(session),
                        "items": session["items"],
                    },
                )
                return
            self._json_response(HTTPStatus.NOT_FOUND, {"error": "Not Found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path not in {"/api/solve", "/api/sessions"}:
                self._json_response(HTTPStatus.NOT_FOUND, {"error": "Not Found"})
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length).decode("utf-8")
                body = json.loads(raw_body)
                if parsed.path == "/api/sessions":
                    created = create_session(str(body.get("name", "")).strip() or None)
                    self._json_response(HTTPStatus.OK, {"session": session_summary(created)})
                    return

                problem_text = str(body.get("problem_text", "")).strip()
                if not problem_text:
                    raise ValueError("problem_text is required")
                if isinstance(body.get("languages"), list):
                    languages = [str(item).strip() for item in body["languages"] if str(item).strip()]
                    if not languages:
                        raise ValueError("At least one language is required")
                else:
                    languages = parse_languages(str(body.get("languages", "")))
                result = solver.solve(problem_text=problem_text, languages=languages).to_dict()

                session_id = str(body.get("session_id", "")).strip()
                session = sessions.get(session_id)
                if not session:
                    session = create_session()

                item = {
                    "problem_text": problem_text,
                    "languages": languages,
                    "result": result,
                }
                session["items"].append(item)
                session["updated_at"] += 1
                session["latest_title"] = result.get("title", "Untitled")

                self._json_response(
                    HTTPStatus.OK,
                    {
                        "result": result,
                        "session": session_summary(session),
                    },
                )
            except ValueError as exc:
                self._json_response(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except json.JSONDecodeError:
                self._json_response(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"})
            except Exception as exc:
                self._json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Solve failed: {exc}"})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def main() -> None:
    load_dotenv_file()
    args = parse_args()
    handler_cls = build_handler(model=args.model, base_url=args.base_url)
    server = ThreadingHTTPServer((args.host, args.port), handler_cls)
    print(f"LeetCode Solver UI running on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from urllib import error, request


@dataclass
class OpenAICompatibleClient:
    model: str
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: float = 90.0
    max_retries: int = 5

    @classmethod
    def from_env(cls, model: str, base_url: str | None = None) -> "OpenAICompatibleClient":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY is not set")
        return cls(model=model, api_key=key, base_url=base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))

    def complete(self, prompt: str) -> str:
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You solve algorithmic problems with precise structured output."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            req = request.Request(
                url=url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=self.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                    data = json.loads(body)
                    return data["choices"][0]["message"]["content"].strip()
            except error.HTTPError as exc:
                retryable = exc.code == 429 or 500 <= exc.code <= 599
                if retryable and attempt < self.max_retries:
                    time.sleep(compute_retry_delay(attempt, exc.headers.get("Retry-After")))
                    last_error = exc
                    continue
                detail = safe_error_body(exc)
                raise RuntimeError(f"API request failed with HTTP {exc.code}: {detail}") from exc
            except error.URLError as exc:
                if attempt < self.max_retries:
                    time.sleep(compute_retry_delay(attempt, None))
                    last_error = exc
                    continue
                raise RuntimeError(f"Network error after retries: {exc}") from exc

        raise RuntimeError(f"API request failed after retries: {last_error}")


def compute_retry_delay(attempt: int, retry_after: str | None) -> float:
    if retry_after:
        try:
            retry_after_value = float(retry_after)
            return max(0.5, min(retry_after_value, 60.0))
        except ValueError:
            pass
    # Exponential backoff with cap: 1, 2, 4, 8, 16, 30...
    return min(30.0, float(2**attempt))


def safe_error_body(exc: error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace").strip()
        return body or exc.reason
    except Exception:
        return str(exc.reason)


def extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])

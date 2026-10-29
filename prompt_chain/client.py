"""HTTP client for OpenAI-compatible chat completion endpoints."""

import json
import urllib.error
import urllib.request


class LLMError(RuntimeError):
    """Raised when the LLM endpoint returns an error or invalid response."""


class LLMClient:
    """Minimal OpenAI-compatible chat completion client (stdlib only).

    Default endpoint is Ollama's OpenAI-compatible server at
    http://localhost:11434/v1. No API keys are used.
    """

    def __init__(self, endpoint=None, model=None, timeout=None, session=None):
        self.endpoint = (endpoint or "http://localhost:11434/v1").rstrip("/")
        self.model = model or "llama3"
        self.timeout = timeout or 60
        self._session = session

    def _request(self, method, path, body=None):
        url = f"{self.endpoint}{path}"
        data = None
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise LLMError(f"endpoint {url} returned HTTP {exc.code}: {body_text}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"could not reach endpoint {url}: {exc}") from exc
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError as exc:
            raise LLMError(f"endpoint {url} returned invalid JSON: {exc}") from exc

    def chat(self, prompt, model=None):
        """Send a single user message and return the assistant's text content."""
        payload = {
            "model": model or self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = self._request("POST", "/chat/completions", body=payload)
        try:
            choices = response["choices"]
            message = choices[0]["message"]
            return message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"unexpected response shape from endpoint: {response!r}") from exc

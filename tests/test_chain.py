"""Mock endpoint tests for prompt-chain-builder-cli.

No network, no API keys. urllib.request.urlopen is patched to return canned
OpenAI-compatible chat completion responses.
"""

import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from prompt_chain.client import LLMClient, LLMError
from prompt_chain.chain import PromptChain
from prompt_chain.config import load_config, write_default_config
from prompt_chain.store import append_results, read_results


def _mock_response(payload, status=200, reason="OK"):
    """Return a context manager behaving like urllib.request.urlopen's result."""
    if isinstance(payload, (dict, list)):
        body = json.dumps(payload).encode("utf-8")
    else:
        body = payload.encode("utf-8") if isinstance(payload, str) else payload
    mock = MagicMock()
    mock.read.return_value = body
    mock.status = status
    mock.reason = reason
    cm = MagicMock()
    cm.__enter__.return_value = mock
    cm.__exit__.return_value = False
    return cm


class LLMClientTests(unittest.TestCase):
    def test_chat_returns_content(self):
        with patch(
            "prompt_chain.client.urllib.request.urlopen",
            return_value=_mock_response(
                {"choices": [{"message": {"content": "hello world"}}]}
            ),
        ):
            client = LLMClient(endpoint="http://localhost:11434/v1", model="test")
            result = client.chat("say hi")
        self.assertEqual(result, "hello world")

    def test_chat_sends_correct_payload(self):
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["body"] = json.loads(req.data)
            captured["timeout"] = timeout
            return _mock_response({"choices": [{"message": {"content": "ok"}}]})

        with patch(
            "prompt_chain.client.urllib.request.urlopen", side_effect=fake_urlopen
        ):
            client = LLMClient(
                endpoint="http://custom.example/v1", model="mymodel", timeout=25
            )
            result = client.chat("prompt text")

        self.assertEqual(result, "ok")
        self.assertEqual(captured["url"], "http://custom.example/v1/chat/completions")
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["body"]["model"], "mymodel")
        self.assertEqual(
            captured["body"]["messages"], [{"role": "user", "content": "prompt text"}]
        )
        self.assertEqual(captured["timeout"], 25)

    def test_chat_http_error_raises(self):
        import urllib.error

        def fake_urlopen(req, timeout=None):
            error = urllib.error.HTTPError(
                "http://x/v1/chat/completions", 500, "boom", {}, io.BytesIO(b"bad")
            )
            raise error

        with patch(
            "prompt_chain.client.urllib.request.urlopen", side_effect=fake_urlopen
        ):
            client = LLMClient()
            with self.assertRaises(LLMError):
                client.chat("x")

    def test_chat_invalid_json_raises(self):
        with patch(
            "prompt_chain.client.urllib.request.urlopen",
            return_value=_mock_response("{not valid json"),
        ):
            client = LLMClient()
            with self.assertRaises(LLMError):
                client.chat("x")

    def test_chat_unexpected_shape_raises(self):
        with patch(
            "prompt_chain.client.urllib.request.urlopen",
            return_value=_mock_response({"choices": []}),
        ):
            client = LLMClient()
            with self.assertRaises(LLMError):
                client.chat("x")


class ChainTests(unittest.TestCase):
    def _capturing_client(self, outputs):
        calls = []

        class FakeClient:
            def chat(self, prompt, model=None):
                calls.append(prompt)
                return outputs[len(calls) - 1]

        return FakeClient(), calls

    def test_output_feeds_next_prompt(self):
        client, calls = self._capturing_client(["first result", "second result"])
        chain = PromptChain(client=client)
        steps = chain.run(["prompt one", "prompt two"])

        self.assertEqual(len(steps), 2)
        self.assertEqual(calls[0], "prompt one")
        self.assertIn("prompt two", calls[1])
        self.assertIn("first result", calls[1])
        self.assertIn("--- Previous output ---", calls[1])
        self.assertEqual(steps[0]["output"], "first result")
        self.assertEqual(steps[1]["output"], "second result")
        self.assertIsNone(steps[0].get("error"))
        self.assertIsNone(steps[1].get("error"))

    def test_single_prompt_no_separator(self):
        client, calls = self._capturing_client(["only"])
        chain = PromptChain(client=client)
        chain.run(["solo"])
        self.assertEqual(calls, ["solo"])

    def test_step_error_recorded(self):
        class FailingClient:
            def chat(self, prompt, model=None):
                raise LLMError("down")

        chain = PromptChain(client=FailingClient())
        steps = chain.run(["a", "b"])
        self.assertEqual(steps[0]["error"], "down")
        self.assertIsNone(steps[0]["output"])
        self.assertEqual(steps[1]["prompt"], "b")
        self.assertEqual(steps[1]["error"], "down")
        self.assertIsNone(steps[1]["output"])


class StoreTests(unittest.TestCase):
    def test_append_and_read_roundtrip(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            append_results(
                path,
                {"endpoint": "http://localhost:11434/v1", "model": "m"},
                [{"index": 1, "prompt": "p", "output": "o", "error": None}],
            )
            append_results(
                path,
                {"endpoint": "http://localhost:11434/v1", "model": "m"},
                [{"index": 2, "prompt": "p2", "output": "o2", "error": None}],
            )
            records = read_results(path)
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["steps"][0]["output"], "o")
            self.assertEqual(records[1]["steps"][0]["output"], "o2")
            self.assertIn("saved_at", records[0])
            self.assertIn("chain", records[0])
        finally:
            os.remove(path)

    def test_read_missing_file(self):
        self.assertEqual(read_results("/nonexistent/path.jsonl"), [])


class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        config = load_config("/nonexistent.json")
        self.assertEqual(config["endpoint"], "http://localhost:11434/v1")
        self.assertEqual(config["model"], "llama3")

    def test_load_from_file(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as handle:
            json.dump(
                {"endpoint": "http://custom/v1", "model": "custom", "timeout": 9},
                handle,
            )
        try:
            config = load_config(path)
            self.assertEqual(config["endpoint"], "http://custom/v1")
            self.assertEqual(config["model"], "custom")
            self.assertEqual(config["timeout"], 9)
        finally:
            os.remove(path)

    def test_write_default_config(self):
        directory = tempfile.mkdtemp()
        path = os.path.join(directory, "pc.json")
        try:
            self.assertTrue(write_default_config(path))
            self.assertFalse(write_default_config(path))
            with open(path) as handle:
                data = json.load(handle)
            self.assertEqual(data["endpoint"], "http://localhost:11434/v1")
        finally:
            os.remove(path)
            os.rmdir(directory)


class CliTests(unittest.TestCase):
    def test_resolve_prompt_plain(self):
        from prompt_chain.cli import _resolve_prompt

        self.assertEqual(_resolve_prompt("hello"), "hello")

    def test_resolve_prompt_file(self):
        from prompt_chain.cli import _resolve_prompt

        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as handle:
            handle.write("file content")
        try:
            self.assertEqual(_resolve_prompt("@" + path), "file content")
        finally:
            os.remove(path)

    def test_parser_run_defaults(self):
        from prompt_chain.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["run", "one", "two", "--output", "out.jsonl"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.prompts, ["one", "two"])
        self.assertEqual(args.output, "out.jsonl")
        self.assertIsNone(args.endpoint)
        self.assertIsNone(args.model)

    def test_parser_config_write(self):
        from prompt_chain.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["config", "--write", "pc.json"])
        self.assertEqual(args.command, "config")
        self.assertEqual(args.write, "pc.json")


if __name__ == "__main__":
    unittest.main()

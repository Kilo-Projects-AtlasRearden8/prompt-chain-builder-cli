# STATUS: prompt-chain-builder-cli

## What was built

A local-first Python CLI tool that chains prompts so each step's output feeds as context into the next step. Uses any OpenAI-compatible endpoint (defaults to Ollama at `http://localhost:11434/v1`). Results are appended to a local JSONL file. Zero external dependencies — standard library only.

### Package structure (`prompt_chain/`)

- `cli.py` — argparse-based CLI with `run` and `config` subcommands
- `client.py` — `LLMClient` using `urllib` for OpenAI-compatible `/chat/completions`
- `chain.py` — `PromptChain` orchestrates steps, appends previous output as context
- `store.py` — `append_results` / `read_results` for JSONL local storage
- `config.py` — loads JSON config from `prompt-chain.json` or `.prompt-chain.json`
- `__main__.py` — enables `python -m prompt_chain` entry point

### CLI commands

```
prompt-chain run "Prompt one" "Prompt two" [--output FILE] [--endpoint URL] [--model NAME] [--config FILE]
prompt-chain run @file1.txt @file2.txt --output results.jsonl
prompt-chain config --write prompt-chain.json
prompt-chain config
```

### Configuration (`prompt-chain.json`)

```json
{
  "endpoint": "http://localhost:11434/v1",
  "model": "llama3",
  "timeout": 60
}
```

CLI flags override config.

### Tests (`tests/test_chain.py`)

17 mock-based tests (no network, no API keys):
- `LLMClientTests` (5): payload shape, error handling, invalid JSON, unexpected response
- `ChainTests` (3): output feeds next prompt, single prompt no separator, step error recorded
- `StoreTests` (2): JSONL append/read roundtrip, missing file returns empty
- `ConfigTests` (3): defaults, load from file, write default config
- `CliTests` (4): prompt resolution (@file), parser args

All pass: `python3 -m unittest discover -s tests -v`

## How to run it

```bash
# From project root
python3 -m prompt_chain run "Write a blog outline" "Write the intro" --output out.jsonl

# With local Ollama running (default endpoint)
python3 -m prompt_chain run @step1.txt @step2.txt

# Show/write config
python3 -m prompt_chain config --write prompt-chain.json
python3 -m prompt_chain config

# Run tests
python3 -m unittest discover -s tests -v
```

## Verification results

- All 17 unit tests pass
- `python3 -m py_compile prompt_chain/*.py` — no syntax errors
- CLI `--help` renders correctly
- `run` subcommand with mocked chain produces expected JSONL output
- `config` subcommand reads/writes config file
- No external dependencies required (stdlib only)

## Known gaps

1. **No real endpoint integration test** — tests use mocks only; manual verification against a running Ollama instance is needed for end-to-end confidence.
2. **Single-threaded, sequential execution** — no parallelism or batching.
3. **Limited prompt templating** — only simple append of previous output; no variable substitution or Jinja-like templates.
4. **No streaming support** — waits for full response; Ollama streaming not used.
5. **No retries/backoff** on transient HTTP errors.
6. **Exit code on partial failure** — returns 1 if any step errors, but still saves all step records to JSONL.
7. **No input validation** for prompt length or model-specific limits.
8. **Config file discovery** only checks two fixed names in CWD; no XDG config dir support.
9. **Python 3.8+ required** (tested on 3.13.5).
10. **Not packaged on PyPI** — run via `python -m prompt_chain` from source.

---

Built for Dylan Asdale, registered nurse turned AI author and founder of Asdale Dynamics, LLC (Indiana, formed October 2026). Credits Asdale Dynamics, LLC. MIT License: Copyright (c) 2026 Asdale Dynamics, LLC.
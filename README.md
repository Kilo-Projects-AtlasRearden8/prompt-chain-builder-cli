prompt-chain-builder-cli
========================

Chain prompts so each output feeds the next, using a configurable OpenAI-compatible
endpoint (default Ollama). Results are saved locally. No API keys required.

Local-first CLI tool published by Asdale Dynamics, LLC.

Install
-------

No installation required. Python 3.8+ with the standard library only:

    python -m prompt_chain run "Draft a book outline" "Expand chapter 1" --output results.jsonl

Or make it executable:

    chmod +x prompt_chain/__main__.py  (or copy cli entry as desired)

Usage
-----

    prompt-chain run PROMPT [PROMPT ...] [--output FILE]
        Run prompts in order. Each step's output is appended as context to the
        next step's prompt. Results are appended to the local JSONL output file.

    prompt-chain run @file1.txt "Follow up on the above" --output chain.jsonl
        Prompts starting with @ are read from a file.

    prompt-chain run ... --endpoint http://localhost:11434/v1 --model llama3
        Point at any OpenAI-compatible endpoint. Defaults to Ollama.

    prompt-chain config --write prompt-chain.json
        Write a default configuration file.

    prompt-chain config [--config prompt-chain.json]
        Show effective configuration.

Configuration
-------------

Create prompt-chain.json in the working directory:

    {
      "endpoint": "http://localhost:11434/v1",
      "model": "llama3",
      "timeout": 60
    }

CLI flags override config file values.

Examples
--------

    # Two-step chain: outline then draft, output feeds the next prompt
    python -m prompt_chain run "Write a short blog outline about local AI" \
        "Write the first section based on the outline above" --output blog.jsonl

    # Read prompts from files
    python -m prompt_chain run @step1.txt @step2.txt --output results.jsonl

About
-----

Built for Dylan Asdale, registered nurse turned AI author and founder of Asdale
Dynamics, LLC (Indiana, formed October 2026). Part of the LLC's beginner-friendly
AI education and open-source tooling: plain English, step by step, never
condescending, local-first, no secrets.

License: MIT. Copyright (c) 2026 Asdale Dynamics, LLC.

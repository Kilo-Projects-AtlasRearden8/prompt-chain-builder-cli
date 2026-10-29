"""Command-line interface for prompt-chain-builder-cli."""

import argparse
import sys

from .chain import PromptChain
from .client import LLMClient, LLMError
from .config import load_config, write_default_config, DEFAULT_ENDPOINT, DEFAULT_MODEL
from .store import append_results


def _resolve_prompt(value):
    """Resolve a prompt argument; values starting with @ are read from a file."""
    if value.startswith("@"):
        path = value[1:]
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()
        except OSError as exc:
            print(f"error: cannot read prompt file {path}: {exc}", file=sys.stderr)
            sys.exit(2)
    return value


def _build_client(endpoint, model, timeout):
    return LLMClient(endpoint=endpoint, model=model, timeout=timeout)


def cmd_run(args):
    prompts = [_resolve_prompt(value) for value in args.prompts]
    if not prompts:
        print("error: at least one prompt is required", file=sys.stderr)
        return 2

    config = load_config(args.config)
    endpoint = args.endpoint or config.get("endpoint")
    model = args.model or config.get("model")
    timeout = config.get("timeout", 60)

    client = _build_client(endpoint, model, timeout)
    chain = PromptChain(client=client)

    try:
        steps = chain.run(prompts, model=model)
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for step in steps:
        if step.get("error"):
            print(f"step {step['index']} failed: {step['error']}", file=sys.stderr)
        else:
            print(f"=== step {step['index']} ===")
            print(step["output"])

    chain_meta = {
        "endpoint": endpoint,
        "model": model,
        "prompt_count": len(prompts),
    }
    if args.output:
        append_results(args.output, chain_meta, steps)
        print(f"\nsaved {len(steps)} step(s) to {args.output}")

    return 0 if not any(step.get("error") for step in steps) else 1


def cmd_config(args):
    if args.write:
        created = write_default_config(args.write)
        if created:
            print(f"wrote default config to {args.write}")
        else:
            print(f"config already exists at {args.write} (not overwritten)")
    else:
        config = load_config(args.config)
        print("endpoint:", config.get("endpoint"))
        print("model:", config.get("model"))
        print("timeout:", config.get("timeout"))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="prompt-chain",
        description="Chain prompts so each output feeds the next, using a local "
        "OpenAI-compatible endpoint (default Ollama). Results saved locally.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run a chain of prompts")
    run_parser.add_argument("prompts", nargs="+", help="prompt text or @file")
    run_parser.add_argument("--output", help="local results file (JSONL)")
    run_parser.add_argument("--endpoint", help="OpenAI-compatible endpoint URL")
    run_parser.add_argument("--model", help="model name")
    run_parser.add_argument("--config", help="config file path")
    run_parser.set_defaults(func=cmd_run)

    config_parser = subparsers.add_parser("config", help="show or write config")
    config_parser.add_argument("--write", help="write default config to this path")
    config_parser.add_argument("--config", help="config file path to show")
    config_parser.set_defaults(func=cmd_config)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

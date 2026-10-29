"""Local-first result storage for prompt chains."""

import json
import os
from datetime import datetime, timezone


def append_results(path, chain_meta, steps):
    """Append a completed chain run to a local JSONL results file.

    Each line is a self-contained JSON object: metadata plus the step results.
    Creates the file (and parent directories) if needed.
    """
    record = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "chain": chain_meta,
        "steps": steps,
    }
    directory = os.path.dirname(os.path.abspath(path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")
    return path


def read_results(path):
    """Read all chain records from a JSONL results file."""
    records = []
    if not os.path.isfile(path):
        return records
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records

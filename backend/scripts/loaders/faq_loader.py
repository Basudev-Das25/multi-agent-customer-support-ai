"""Loader for ``sample_faq.json`` — a small set of FAQ entries."""

import json
from pathlib import Path

from scripts.loaders.base import DocumentInput


def FaqLoader(path: str | Path) -> list[DocumentInput]:  # noqa: N802
    """Load FAQ entries from a JSON file.

    Expected format (JSON array)::

        [
          {"id": "faq-1", "question": "...", "answer": "..."},
          ...
        ]

    Returns a single document containing all FAQ entries.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(raw, list):
        raise ValueError("FAQ file must contain a JSON array.")

    entries: list[str] = []
    for entry in raw:
        q = entry.get("question", "")
        a = entry.get("answer", "")
        if q and a:
            entries.append(f"Q: {q}\nA: {a}")

    if not entries:
        raise ValueError("No valid FAQ entries found.")

    text = "\n\n".join(entries)

    return [
        DocumentInput(
            title="Frequently Asked Questions",
            category="faq",
            source="sample_faq",
            text=text,
            metadata={"record_count": str(len(entries))},
        ),
    ]

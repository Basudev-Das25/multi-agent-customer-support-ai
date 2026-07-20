"""Loader for SQuAD v1.1 — reading comprehension dataset with Wikipedia passages."""

import json
from pathlib import Path

from scripts.loaders.base import DocumentInput


def SquadLoader(  # noqa: N802
    path: str | Path,
    *,
    sample: int | None = None,
) -> list[DocumentInput]:
    """Load the SQuAD v1.1 dataset from a local JSON file.

    Expected JSON structure (SQuAD format)::

        {"data": [{"title": "...", "paragraphs": [
            {"context": "...", "qas": [{"question": "...", "answers": [...]}]},
        ]}]}

    Returns one document per Wikipedia article.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    if not isinstance(raw, dict) or "data" not in raw:
        raise ValueError("SQuAD file must contain a JSON object with a 'data' key.")

    articles = raw["data"]
    if sample is not None:
        articles = articles[:sample]

    documents: list[DocumentInput] = []
    for article in articles:
        title = article.get("title", "Untitled")
        paragraphs = article.get("paragraphs", [])

        sections: list[str] = []
        for para in paragraphs:
            context = para.get("context", "").strip()
            qas = para.get("qas", [])

            if not context:
                continue

            section = [f"Context: {context}"]
            for qa in qas[:5]:  # limit QA pairs per paragraph to avoid bloat
                question = qa.get("question", "").strip()
                answers = qa.get("answers", [])
                if question and answers:
                    answer = answers[0].get("text", "")
                    section.append(f"Q: {question}")
                    section.append(f"A: {answer}")
            sections.append("\n".join(section))

        if not sections:
            continue

        documents.append(
            DocumentInput(
                title=title,
                category="general_knowledge",
                source="squad_v1.1",
                text="\n\n".join(sections),
                metadata={"article_title": title},
            ),
        )

    return documents

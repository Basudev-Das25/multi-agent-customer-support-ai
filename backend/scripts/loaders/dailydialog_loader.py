"""Loader for XDailyDialog (English) — multi-turn open-domain dialogues."""

from pathlib import Path

from scripts.loaders.base import DocumentInput


def DailyDialogLoader(  # noqa: N802
    path: str | Path,
    *,
    sample: int | None = None,
) -> list[DocumentInput]:
    """Load the English portion of XDailyDialog from a text file.

    Expected format (tab-separated)::

        utterance1 __eou__ utterance2 __eou__ ... \\t topic \\t actions \\t emotions

    Returns one document per dialogue.
    """
    text = Path(path).read_text(encoding="utf-8")
    lines = text.strip().splitlines()

    if sample is not None:
        lines = lines[:sample]

    documents: list[DocumentInput] = []
    for idx, line in enumerate(lines):
        if not line.strip():
            continue

        parts = line.split("\t")
        if not parts:
            continue

        utterances_raw = parts[0]
        utterances = utterances_raw.replace(" __eou__ ", "\n").replace("__eou__", "")
        utterances = utterances.strip()

        if not utterances:
            continue

        # Build topic metadata if available.
        topic_id = parts[1].strip() if len(parts) > 1 else ""
        meta: dict[str, str] = {"dialogue_id": str(idx)}
        if topic_id:
            meta["topic_id"] = topic_id

        documents.append(
            DocumentInput(
                title=f"Dialogue {idx}",
                category=f"topic_{topic_id}" if topic_id else "conversation",
                source="xdailydialog_en",
                text=utterances,
                metadata=meta,
            ),
        )

    return documents

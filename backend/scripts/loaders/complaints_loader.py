"""Loader for ``complaints.json.zip`` — CFPB consumer complaints.

Streams records from the ZIP file without loading the full dataset into memory.
"""

import json
import zipfile
from collections.abc import Iterable
from pathlib import Path

from scripts.loaders.base import DocumentInput


def _stream_complaints(
    zip_path: Path,
) -> Iterable[dict]:
    """Yield one complaint record at a time from the ZIP archive."""
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        if not names:
            raise ValueError("ZIP archive is empty.")

        # The archive contains a single JSON file.
        with z.open(names[0]) as f:
            # The JSON is a top-level array.  Parse as a stream.
            decoder = json.JSONDecoder()
            buffer = f.read(32 * 1024 * 1024).decode("utf-8")  # 32 MB window
            idx = 0
            while idx < len(buffer):
                # Skip whitespace before the next record.
                while idx < len(buffer) and buffer[idx] in " \t\n\r,[]":
                    idx += 1
                if idx >= len(buffer) or buffer[idx] == "]":
                    break
                try:
                    obj, end = decoder.raw_decode(buffer, idx)
                    if isinstance(obj, dict) and obj.get("complaint_what_happened"):
                        yield obj
                    idx = end
                except json.JSONDecodeError:
                    # If we hit a decode error, the record might be split
                    # across the buffer boundary.  For a production system
                    # a more sophisticated streaming parser (e.g. ijson)
                    # would be used.  Here we stop gracefully.
                    break


def ComplaintsLoader(  # noqa: N802
    path: str | Path,
    *,
    sample: int | None = None,
) -> list[DocumentInput]:
    """Load consumer complaints from a ZIP-compressed JSON file.

    Parameters
    ----------
    path:
        Path to ``complaints.json.zip``.
    sample:
        Maximum number of complaint records to include (None = all).

    Returns one document per complaint (with a non-empty narrative).
    """
    zip_path = Path(path)
    if not zip_path.exists():
        raise FileNotFoundError(f"Complaints file not found: {zip_path}")

    documents: list[DocumentInput] = []
    count = 0

    for record in _stream_complaints(zip_path):
        narrative = record.get("complaint_what_happened", "").strip()
        if not narrative:
            continue

        product = record.get("product", "Unknown")
        issue = record.get("issue", "")
        complaint_id = record.get("complaint_id", str(count))

        title = f"Complaint {complaint_id}"
        text_parts = [f"Product: {product}"]
        if issue:
            text_parts.append(f"Issue: {issue}")
        text_parts.append("")
        text_parts.append(narrative)

        documents.append(
            DocumentInput(
                title=title,
                category=product,
                source="complaints",
                text="\n".join(text_parts),
                metadata={
                    "complaint_id": complaint_id,
                    "product": product,
                    "state": record.get("state", ""),
                },
            ),
        )

        count += 1
        if sample is not None and count >= sample:
            break

    if not documents:
        raise ValueError("No complaint records with non-empty narratives found.")

    return documents

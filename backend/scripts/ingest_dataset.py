#!/usr/bin/env python3
"""
Dataset ingestion CLI.

Ingests structured datasets directly into the knowledge base without
going through the PDF upload path.

Usage examples::

    # FAQ sample
    python scripts/ingest_dataset.py --dataset faq --path datasets/sample_faq.json

    # Banking77 (fetched from HuggingFace)
    python scripts/ingest_dataset.py --dataset banking77

    # SQuAD v1.1
    python scripts/ingest_dataset.py --dataset squad --path datasets/train-v1.1.json

    # SQuAD v1.1 (first 5 articles only)
    python scripts/ingest_dataset.py --dataset squad \\
        --path datasets/train-v1.1.json --sample 5

    # XDailyDialog English
    python scripts/ingest_dataset.py --dataset dailydialog \\
        --path datasets/XDailyDialog/data/en_train_human.txt

    # Complaints (stream from ZIP)
    python scripts/ingest_dataset.py --dataset complaints \\
        --path complaints.json.zip --sample 5000
"""

import argparse
import asyncio
import sys
import time

# Ensure the backend package is importable.
from pathlib import Path

# Add the backend root to sys.path so ``app`` and ``scripts`` can be imported
# regardless of the working directory.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.database.client import database  # noqa: E402
from scripts.builders.knowledge_document_builder import (  # noqa: E402
    format_summary,
    ingest_documents,
)
from scripts.loaders import (  # noqa: E402
    Banking77Loader,
    ComplaintsLoader,
    DailyDialogLoader,
    FaqLoader,
    SquadLoader,
)

# ---------------------------------------------------------------------------
# Progress display
# ---------------------------------------------------------------------------


def _print_progress(result, total_chunks, start_time):  # noqa: ANN001
    elapsed = time.monotonic() - start_time
    docs_per_sec = result.total / elapsed if elapsed > 0 else 0
    sys.stderr.write(
        f"\r  Processed {result.total} docs · "
        f"{total_chunks} chunks · "
        f"{elapsed:.1f}s · "
        f"{docs_per_sec:.1f} docs/s"
    )
    sys.stderr.flush()


# ---------------------------------------------------------------------------
# Loader registry
# ---------------------------------------------------------------------------

LOADERS: dict[str, tuple] = {
    "faq": (FaqLoader, True),
    "banking77": (Banking77Loader, False),
    "squad": (SquadLoader, True),
    "dailydialog": (DailyDialogLoader, True),
    "complaints": (ComplaintsLoader, True),
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:  # noqa: C901
    parser = argparse.ArgumentParser(
        description="Ingest a dataset into the knowledge base.",
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=list(LOADERS),
        help="Dataset to ingest.",
    )
    parser.add_argument(
        "--path",
        default=None,
        help=(
            "Path to the dataset file (required for faq, squad, dailydialog, "
            "complaints; ignored for banking77 which fetches from HuggingFace)."
        ),
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Limit to the first N records (documents for most datasets).",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help=(
            "MongoDB ObjectId of the admin user that owns the ingested "
            "documents.  Defaults to the first admin user found in the "
            "database if not provided."
        ),
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Resolve path
    # ------------------------------------------------------------------
    loader_cls, needs_path = LOADERS[args.dataset]
    dataset_path: str | Path | None = args.path

    if needs_path and not dataset_path:
        parser.error(f"--path is required for dataset '{args.dataset}'.")

    if dataset_path is not None:
        dataset_path = Path(dataset_path)
        if not dataset_path.exists():
            parser.error(f"Path does not exist: {dataset_path}")

    # ------------------------------------------------------------------
    # Connect to MongoDB
    # ------------------------------------------------------------------
    print("Connecting to MongoDB...", file=sys.stderr)
    await database.connect()

    try:
        # ------------------------------------------------------------------
        # Resolve user
        # ------------------------------------------------------------------
        user_id = args.user_id
        if user_id is None:
            # Use the first admin user in the database.
            from app.database.collections import get_users_collection

            users = get_users_collection()
            admin = await users.find_one({"role": "admin"})
            if admin is None:
                print(
                    "No admin user found.  Register an admin first or pass --user-id.",
                    file=sys.stderr,
                )
                sys.exit(1)
            user_id = str(admin["_id"])
            print(f"Using admin user: {admin['email']} ({user_id})", file=sys.stderr)

        # ------------------------------------------------------------------
        # Load
        # ------------------------------------------------------------------
        print(f"Loading dataset '{args.dataset}'...", file=sys.stderr)
        loader_kwargs = {}
        if dataset_path is not None:
            loader_kwargs["path"] = dataset_path
        if args.sample is not None:
            loader_kwargs["sample"] = args.sample

        documents = loader_cls(**loader_kwargs)  # type: ignore[arg-type]
        print(f"  → {len(documents)} documents loaded", file=sys.stderr)

        if not documents:
            print("Nothing to ingest.", file=sys.stderr)
            return

        # ------------------------------------------------------------------
        # Ingest
        # ------------------------------------------------------------------
        print("Ingesting...", file=sys.stderr)
        result = await ingest_documents(
            documents,
            user_id=user_id,
            progress_callback=_print_progress,
        )

        # Final newline after progress output.
        print(file=sys.stderr)

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        print(format_summary(result, 0), file=sys.stderr)

        if result.failed:
            sys.exit(1)

    finally:
        await database.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

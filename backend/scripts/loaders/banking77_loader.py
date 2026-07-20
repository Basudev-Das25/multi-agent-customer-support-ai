"""Loader for BANKING77 — 13 083 customer queries labelled with 77 intents."""

import csv
import io
from collections import defaultdict
from urllib.request import urlopen

from scripts.loaders.base import DocumentInput

# The official HuggingFace hosting URL for the dataset CSV files.
_TRAIN_URL = (
    "https://raw.githubusercontent.com/PolyAI-LDN/"
    "task-specific-datasets/master/banking_data/train.csv"
)
_TEST_URL = (
    "https://raw.githubusercontent.com/PolyAI-LDN/"
    "task-specific-datasets/master/banking_data/test.csv"
)

# Mapping from label index → intent name (from the dataset card).
_INTENT_NAMES = [
    "activate_my_card",
    "age_limit",
    "apple_pay_or_google_pay",
    "atm_support",
    "automatic_top_up",
    "balance_not_updated_after_bank_transfer",
    "balance_not_updated_after_cheque_or_cash_deposit",
    "beneficiary_not_allowed",
    "cancel_transfer",
    "card_about_to_expire",
    "card_acceptance",
    "card_arrival",
    "card_delivery_estimate",
    "card_linking",
    "card_not_working",
    "card_payment_fee_charged",
    "card_payment_not_recognised",
    "card_payment_wrong_exchange_rate",
    "card_swallowed",
    "cash_withdrawal_charge",
    "cash_withdrawal_not_recognised",
    "change_pin",
    "compromised_card",
    "contactless_not_working",
    "country_support",
    "declined_card_payment",
    "declined_cash_withdrawal",
    "declined_transfer",
    "direct_debit_payment_not_recognised",
    "disposable_card_limits",
    "edit_personal_details",
    "exchange_charge",
    "exchange_rate",
    "exchange_via_app",
    "extra_charge_on_statement",
    "failed_transfer",
    "fiat_currency_support",
    "get_disposable_virtual_card",
    "get_physical_card",
    "getting_spare_card",
    "getting_virtual_card",
    "lost_or_stolen_card",
    "lost_or_stolen_phone",
    "order_physical_card",
    "passcode_forgotten",
    "pending_card_payment",
    "pending_cash_withdrawal",
    "pending_top_up",
    "pending_transfer",
    "pin_blocked",
    "receiving_money",
    "Refund_not_showing_up",
    "request_refund",
    "reverted_card_payment",
    "supported_cards_and_currencies",
    "terminate_account",
    "top_up_by_bank_transfer_charge",
    "top_up_by_card_charge",
    "top_up_by_cash_or_cheque",
    "top_up_failed",
    "top_up_limits",
    "top_up_reverted",
    "topping_up_by_card",
    "transaction_charged_twice",
    "transfer_fee_charged",
    "transfer_into_account",
    "transfer_not_received_by_recipient",
    "transfer_timing",
    "unable_to_verify_identity",
    "verify_my_identity",
    "verify_source_of_funds",
    "verify_top_up",
    "virtual_card_not_working",
    "visa_or_mastercard",
    "why_verify_identity",
    "wrong_amount_of_cash_received",
    "wrong_exchange_rate_for_cash_withdrawal",
]


def _fetch_csv(url: str) -> list[dict[str, str]]:
    """Fetch a remote CSV file and return its rows as dicts."""
    with urlopen(url) as resp:  # noqa: S310
        text = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


def Banking77Loader(  # noqa: N802
    path: str | None = None,
    *,
    sample: int | None = None,
) -> list[DocumentInput]:
    """Load the BANKING77 dataset.

    Parameters
    ----------
    path:
        Ignored — data is fetched from the official HuggingFace URLs.
    sample:
        If set, limit to the first *sample* rows (combined train + test).

    Returns one document per intent category containing all example queries.
    """
    train_rows = _fetch_csv(_TRAIN_URL)
    test_rows = _fetch_csv(_TEST_URL)

    rows = train_rows + test_rows

    if sample is not None:
        rows = rows[:sample]

    # Group queries by intent.
    # The upstream CSV may use either "category" (intent name string)
    # or "label" (integer index) depending on the version.
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if "category" in row and row["category"].strip():
            # New format: category is the intent name string.
            intent_name = row["category"].strip()
        elif "label" in row:
            # Legacy format: label is an integer index.
            label_idx = int(row["label"])
            intent_name = (
                _INTENT_NAMES[label_idx]
                if label_idx < len(_INTENT_NAMES)
                else f"intent_{label_idx}"
            )
        else:
            continue
        groups[intent_name].append(row["text"])

    documents: list[DocumentInput] = []
    for intent in sorted(groups):
        texts = groups[intent]

        body = "\n\n".join(f"Example query: {t}" for t in texts)
        description = (
            f"Banking intent category: {intent}\n"
            f"Total example queries: {len(texts)}\n\n"
            f"{body}"
        )

        documents.append(
            DocumentInput(
                title=intent,
                category=intent,
                source="banking77",
                text=description,
                metadata={"intent": intent, "example_count": str(len(texts))},
            ),
        )

    return documents

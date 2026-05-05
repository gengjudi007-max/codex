from __future__ import annotations

from pathlib import Path

from codex.services.transaction_data_parser import convert_transaction_csv_to_json


DEFAULT_INPUT = Path("data/import/transaction/transaction_data.csv")
DEFAULT_OUTPUT = Path("data/processed/transaction_items.json")


def run():
    output = convert_transaction_csv_to_json(DEFAULT_INPUT, DEFAULT_OUTPUT)
    print(f"Transaction data converted → {output}")


if __name__ == "__main__":
    run()

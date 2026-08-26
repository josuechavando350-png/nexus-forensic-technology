from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Transaction:
    transaction_id: str
    source_account: str
    target_account: str
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not self.transaction_id.strip():
            raise ValueError("transaction_id must not be blank")
        if not self.source_account.strip() or not self.target_account.strip():
            raise ValueError("accounts must not be blank")
        if self.amount < 0:
            raise ValueError("amount must be non-negative")
        if len(self.currency.strip()) != 3:
            raise ValueError("currency must be a 3-letter code")


def aggregate_flows(transactions: Iterable[Transaction]) -> dict[tuple[str, str, str], Decimal]:
    totals: dict[tuple[str, str, str], Decimal] = {}
    seen_ids: set[str] = set()
    for tx in transactions:
        if tx.transaction_id in seen_ids:
            raise ValueError(f"duplicate transaction_id: {tx.transaction_id}")
        seen_ids.add(tx.transaction_id)
        key = (tx.source_account, tx.target_account, tx.currency.upper())
        totals[key] = totals.get(key, Decimal("0")) + tx.amount
    return dict(sorted(totals.items()))


def account_net_flow(transactions: Iterable[Transaction], account: str, currency: str) -> Decimal:
    currency = currency.upper()
    net = Decimal("0")
    for tx in transactions:
        if tx.currency.upper() != currency:
            continue
        if tx.target_account == account:
            net += tx.amount
        if tx.source_account == account:
            net -= tx.amount
    return net

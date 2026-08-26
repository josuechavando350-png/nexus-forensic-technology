from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Web3Adapter:
    web3: Any

    def transaction(self, tx_hash: str) -> dict[str, Any]:
        if not tx_hash.strip():
            raise ValueError("tx_hash must not be blank")
        tx = self.web3.eth.get_transaction(tx_hash)
        return dict(tx)

    def receipt(self, tx_hash: str) -> dict[str, Any]:
        if not tx_hash.strip():
            raise ValueError("tx_hash must not be blank")
        receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        return dict(receipt)

    def balance(self, address: str, block_identifier: str | int = "latest") -> int:
        if not address.strip():
            raise ValueError("address must not be blank")
        checksum = self.web3.to_checksum_address(address)
        return int(self.web3.eth.get_balance(checksum, block_identifier=block_identifier))

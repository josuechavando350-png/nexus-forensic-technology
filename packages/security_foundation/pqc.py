from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import Final

from pqcrypto.sign.ml_dsa_65 import keygen, sign, verify
from pqcrypto.sign.ml_dsa_65 import InvalidSignatureError

ALGORITHM: Final[str] = "ML-DSA-65"
CONTEXT: Final[bytes] = b"NEXUS-EVIDENCE-CUSTODY-v1"


@dataclass(frozen=True, slots=True)
class PQCSignatureBundle:
    algorithm: str
    evidence_sha3_256: str
    public_key_b64: str
    signature_b64: str


class MLDSA65EvidenceSigner:
    """NIST FIPS 204 ML-DSA-65 signing for evidence-integrity records."""

    def __init__(self, public_key: bytes, secret_key: bytes) -> None:
        if not public_key:
            raise ValueError("public_key must not be empty")
        if not secret_key:
            raise ValueError("secret_key must not be empty")
        self._public_key = bytes(public_key)
        self._secret_key = bytes(secret_key)

    @classmethod
    def generate(cls) -> "MLDSA65EvidenceSigner":
        try:
            public_key, secret_key = keygen()
        except Exception as exc:
            raise RuntimeError("ML-DSA-65 key generation failed") from exc
        return cls(public_key=public_key, secret_key=secret_key)

    @property
    def public_key(self) -> bytes:
        return self._public_key

    def sign_evidence(self, evidence: bytes) -> PQCSignatureBundle:
        if not isinstance(evidence, bytes):
            raise TypeError("evidence must be bytes")
        digest = hashlib.sha3_256(evidence).digest()
        try:
            signature = sign(self._secret_key, digest, CONTEXT)
        except Exception as exc:
            raise RuntimeError("ML-DSA-65 signing failed") from exc
        return PQCSignatureBundle(
            algorithm=ALGORITHM,
            evidence_sha3_256=digest.hex(),
            public_key_b64=base64.b64encode(self._public_key).decode("ascii"),
            signature_b64=base64.b64encode(signature).decode("ascii"),
        )

    @staticmethod
    def verify_evidence(evidence: bytes, bundle: PQCSignatureBundle) -> bool:
        if not isinstance(evidence, bytes):
            raise TypeError("evidence must be bytes")
        if bundle.algorithm != ALGORITHM:
            return False
        digest = hashlib.sha3_256(evidence).digest()
        if digest.hex() != bundle.evidence_sha3_256:
            return False
        try:
            public_key = base64.b64decode(bundle.public_key_b64, validate=True)
            signature = base64.b64decode(bundle.signature_b64, validate=True)
            verify(public_key, digest, signature, CONTEXT)
        except (ValueError, InvalidSignatureError):
            return False
        except Exception as exc:
            raise RuntimeError("ML-DSA-65 verification failed") from exc
        return True

from __future__ import annotations

import json
from urllib.parse import quote, urljoin

from .specs import CommandSpec, RequestSpec, require_nonblank, require_safe_local_path


def vault_transit_sign_request(base_url: str, key_name: str, base64_input: str, token: str) -> RequestSpec:
    base = require_nonblank(base_url, "base_url")
    if not base.endswith("/"):
        base += "/"
    body = json.dumps({"input": require_nonblank(base64_input, "base64_input")}, sort_keys=True, separators=(",", ":")).encode()
    return RequestSpec("POST", urljoin(base, f"v1/transit/sign/{quote(require_nonblank(key_name, 'key_name'), safe='')}"), (("X-Vault-Token", require_nonblank(token, "token")), ("Content-Type", "application/json")), body)


def s3_object_lock_configuration_request(endpoint: str, bucket: str, retain_days: int) -> RequestSpec:
    if retain_days <= 0:
        raise ValueError("retain_days must be positive")
    base = require_nonblank(endpoint, "endpoint")
    if not base.endswith("/"):
        base += "/"
    bucket_name = quote(require_nonblank(bucket, "bucket"), safe="")
    body = ("<ObjectLockConfiguration><ObjectLockEnabled>Enabled</ObjectLockEnabled><Rule><DefaultRetention><Mode>COMPLIANCE</Mode>" f"<Days>{retain_days}</Days></DefaultRetention></Rule></ObjectLockConfiguration>").encode()
    return RequestSpec("POST", urljoin(base, f"{bucket_name}?object-lock"), (("Content-Type", "application/xml"),), body)


def sigstore_verify_command(artifact_path: str, signature_path: str, certificate_path: str) -> CommandSpec:
    return CommandSpec(("cosign", "verify-blob", "--signature", require_safe_local_path(signature_path, "signature_path"), "--certificate", require_safe_local_path(certificate_path, "certificate_path"), require_safe_local_path(artifact_path, "artifact_path")))


def restic_check_command(repository: str) -> CommandSpec:
    return CommandSpec(("restic", "-r", require_safe_local_path(repository, "repository"), "check"))


def pkcs11_uri(token_label: str, object_label: str) -> str:
    token = quote(require_nonblank(token_label, "token_label"), safe="")
    obj = quote(require_nonblank(object_label, "object_label"), safe="")
    return f"pkcs11:token={token};object={obj};type=private"

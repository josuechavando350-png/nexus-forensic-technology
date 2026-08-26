from __future__ import annotations

from .specs import CommandSpec, require_safe_local_path


def openssl_sign_command(private_key: str, input_path: str, signature_path: str) -> CommandSpec:
    return CommandSpec(("openssl", "dgst", "-sha256", "-sign", require_safe_local_path(private_key, "private_key"), "-out", require_safe_local_path(signature_path, "signature_path"), require_safe_local_path(input_path, "input_path")), read_only=False)


def openssl_verify_command(public_key: str, input_path: str, signature_path: str) -> CommandSpec:
    return CommandSpec(("openssl", "dgst", "-sha256", "-verify", require_safe_local_path(public_key, "public_key"), "-signature", require_safe_local_path(signature_path, "signature_path"), require_safe_local_path(input_path, "input_path")))


def openssl_timestamp_query_command(input_path: str, query_path: str) -> CommandSpec:
    return CommandSpec(("openssl", "ts", "-query", "-data", require_safe_local_path(input_path, "input_path"), "-sha256", "-cert", "-out", require_safe_local_path(query_path, "query_path")), read_only=False)


def git_version_command(path: str) -> CommandSpec:
    return CommandSpec(("git", "-C", require_safe_local_path(path, "path"), "rev-parse", "HEAD"))


def dvc_status_command(path: str) -> CommandSpec:
    return CommandSpec(("dvc", "status", "--project", require_safe_local_path(path, "path")))

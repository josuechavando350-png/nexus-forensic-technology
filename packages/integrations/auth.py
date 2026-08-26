from __future__ import annotations

import json
from urllib.parse import urljoin

from .specs import RequestSpec, require_nonblank


def oidc_discovery_request(issuer_url: str) -> RequestSpec:
    issuer = require_nonblank(issuer_url, "issuer_url")
    base = issuer if issuer.endswith("/") else issuer + "/"
    return RequestSpec("GET", urljoin(base, ".well-known/openid-configuration"), (("Accept", "application/json"),))


def oidc_userinfo_request(userinfo_endpoint: str, access_token: str) -> RequestSpec:
    return RequestSpec("GET", require_nonblank(userinfo_endpoint, "userinfo_endpoint"), (("Authorization", f"Bearer {require_nonblank(access_token, 'access_token')}"), ("Accept", "application/json")))


def webauthn_assertion_payload(*, challenge: str, credential_id: str, client_data_json: str, authenticator_data: str, signature: str) -> bytes:
    values = {"challenge": require_nonblank(challenge, "challenge"), "credential_id": require_nonblank(credential_id, "credential_id"), "client_data_json": require_nonblank(client_data_json, "client_data_json"), "authenticator_data": require_nonblank(authenticator_data, "authenticator_data"), "signature": require_nonblank(signature, "signature")}
    return json.dumps(values, sort_keys=True, separators=(",", ":")).encode()

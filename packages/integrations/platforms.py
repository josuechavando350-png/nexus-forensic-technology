from __future__ import annotations

import json
from urllib.parse import quote, urlencode, urljoin

from .specs import RequestSpec, require_nonblank


def _base(base_url: str) -> str:
    value = require_nonblank(base_url, "base_url")
    return value if value.endswith("/") else value + "/"


def thehive_case_request(base_url: str, case_id: str, api_key: str) -> RequestSpec:
    key = require_nonblank(api_key, "api_key")
    url = urljoin(_base(base_url), f"api/v1/case/{quote(require_nonblank(case_id, 'case_id'), safe='')}")
    return RequestSpec("GET", url, (("Authorization", f"Bearer {key}"), ("Accept", "application/json")))


def velociraptor_query_request(base_url: str, artifact: str, api_key: str) -> RequestSpec:
    key = require_nonblank(api_key, "api_key")
    payload = json.dumps({"artifact": require_nonblank(artifact, "artifact")}, sort_keys=True, separators=(",", ":")).encode()
    return RequestSpec("POST", urljoin(_base(base_url), "api/v1/GetTable"), (("Authorization", f"Bearer {key}"), ("Content-Type", "application/json")), payload)


def opencti_indicator_request(base_url: str, indicator_id: str, api_key: str) -> RequestSpec:
    key = require_nonblank(api_key, "api_key")
    payload = json.dumps({"query": "query Indicator($id: ID!) { indicator(id: $id) { id name pattern } }", "variables": {"id": require_nonblank(indicator_id, "indicator_id")}}, sort_keys=True, separators=(",", ":")).encode()
    return RequestSpec("POST", urljoin(_base(base_url), "graphql"), (("Authorization", f"Bearer {key}"), ("Content-Type", "application/json")), payload)


def misp_attribute_request(base_url: str, value: str, api_key: str) -> RequestSpec:
    key = require_nonblank(api_key, "api_key")
    query = urlencode({"value": require_nonblank(value, "value")})
    return RequestSpec("GET", urljoin(_base(base_url), f"attributes/restSearch?{query}"), (("Authorization", key), ("Accept", "application/json")))


def censys_host_request(base_url: str, ip: str, token: str) -> RequestSpec:
    headers = (("Authorization", f"Bearer {require_nonblank(token, 'token')}"), ("Accept", "application/json"))
    return RequestSpec("GET", urljoin(_base(base_url), f"api/v2/hosts/{quote(require_nonblank(ip, 'ip'), safe='')}"), headers)


def shodan_host_request(base_url: str, ip: str, api_key: str) -> RequestSpec:
    query = urlencode({"key": require_nonblank(api_key, "api_key")})
    return RequestSpec("GET", urljoin(_base(base_url), f"shodan/host/{quote(require_nonblank(ip, 'ip'), safe='')}?{query}"))


def urlhaus_url_request(base_url: str, url_value: str) -> RequestSpec:
    body = urlencode({"url": require_nonblank(url_value, "url_value")}).encode()
    return RequestSpec("POST", urljoin(_base(base_url), "v1/url/"), (("Content-Type", "application/x-www-form-urlencoded"),), body)


def virustotal_url_request(base_url: str, url_id: str, api_key: str) -> RequestSpec:
    return RequestSpec("GET", urljoin(_base(base_url), f"api/v3/urls/{quote(require_nonblank(url_id, 'url_id'), safe='')}"), (("x-apikey", require_nonblank(api_key, "api_key")), ("Accept", "application/json")))


def official_social_profile_request(base_url: str, profile_id: str, bearer_token: str) -> RequestSpec:
    return RequestSpec("GET", urljoin(_base(base_url), f"profiles/{quote(require_nonblank(profile_id, 'profile_id'), safe='')}"), (("Authorization", f"Bearer {require_nonblank(bearer_token, 'bearer_token')}"), ("Accept", "application/json")))


def qdrant_search_request(base_url: str, collection: str, vector: tuple[float, ...], limit: int = 10) -> RequestSpec:
    if not vector:
        raise ValueError("vector must not be empty")
    if limit <= 0:
        raise ValueError("limit must be positive")
    body = json.dumps({"vector": list(vector), "limit": limit, "with_payload": True}, sort_keys=True, separators=(",", ":")).encode()
    url = urljoin(_base(base_url), f"collections/{quote(require_nonblank(collection, 'collection'), safe='')}/points/search")
    return RequestSpec("POST", url, (("Content-Type", "application/json"),), body)

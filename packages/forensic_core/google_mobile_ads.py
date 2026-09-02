from __future__ import annotations

import plistlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_ANDROID_NS = "http://schemas.android.com/apk/res/android"
_ANDROID_NAME = f"{{{_ANDROID_NS}}}name"
_ANDROID_VALUE = f"{{{_ANDROID_NS}}}value"
_GAD_APP_ID = re.compile(r"^ca-app-pub-\d{16}~\d{10}$")
_GRADLE_ADS = re.compile(
    r"com\.google\.android\.gms:(play-services-ads(?:-lite)?):([0-9]+(?:\.[0-9]+){1,3}(?:[-+A-Za-z0-9.]*)?)"
)
_POD_ADS = re.compile(
    r"^\s*-\s+Google-Mobile-Ads-SDK\s+\(([^)]+)\)", re.MULTILINE
)
_SKAD_ID = re.compile(r"^[a-z0-9]{10}\.skadnetwork$")
_MAX_EVIDENCE_BYTES = 16 * 1024 * 1024


class MobileAdsEvidenceError(ValueError):
    """Raised when Google Mobile Ads configuration evidence is invalid."""


@dataclass(frozen=True, slots=True)
class AndroidMobileAdsEvidence:
    application_id: str | None
    permissions: tuple[str, ...]
    sdk_dependencies: tuple[tuple[str, str], ...]
    delay_app_measurement_init: bool | None


@dataclass(frozen=True, slots=True)
class IOSMobileAdsEvidence:
    application_id: str | None
    sdk_version: str | None
    skadnetwork_ids: tuple[str, ...]
    delay_app_measurement_init: bool | None
    is_ad_manager_app: bool | None


def _bounded_text(path: str | Path) -> str:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.stat().st_size > _MAX_EVIDENCE_BYTES:
        raise MobileAdsEvidenceError("mobile ads evidence exceeds 16 MiB")
    return source.read_text(encoding="utf-8-sig")


def _validate_application_id(value: object, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MobileAdsEvidenceError(f"{field} must be a string")
    if not _GAD_APP_ID.fullmatch(value):
        raise MobileAdsEvidenceError(f"{field} is not a valid Google Mobile Ads application ID")
    return value


def parse_android_manifest(text: str) -> tuple[str | None, tuple[str, ...], bool | None]:
    """Extract Google Mobile Ads metadata from an Android manifest."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise MobileAdsEvidenceError("invalid AndroidManifest.xml") from exc
    if root.tag != "manifest":
        raise MobileAdsEvidenceError("Android evidence root must be <manifest>")

    permissions = sorted(
        {
            element.attrib[_ANDROID_NAME]
            for element in root.findall("uses-permission")
            if element.attrib.get(_ANDROID_NAME)
        }
    )

    application = root.find("application")
    application_id: str | None = None
    delay_measurement: bool | None = None
    if application is not None:
        for metadata in application.findall("meta-data"):
            name = metadata.attrib.get(_ANDROID_NAME)
            value = metadata.attrib.get(_ANDROID_VALUE)
            if name == "com.google.android.gms.ads.APPLICATION_ID":
                if application_id is not None:
                    raise MobileAdsEvidenceError("duplicate Mobile Ads APPLICATION_ID metadata")
                application_id = _validate_application_id(value, field="Android APPLICATION_ID")
            elif name == "com.google.android.gms.ads.DELAY_APP_MEASUREMENT_INIT":
                if value not in {"true", "false"}:
                    raise MobileAdsEvidenceError(
                        "DELAY_APP_MEASUREMENT_INIT must be true or false"
                    )
                delay_measurement = value == "true"

    return application_id, tuple(permissions), delay_measurement


def parse_gradle_dependencies(text: str) -> tuple[tuple[str, str], ...]:
    """Extract pinned Google Mobile Ads Maven artifacts from Gradle evidence."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    dependencies = {(match.group(1), match.group(2)) for match in _GRADLE_ADS.finditer(text)}
    return tuple(sorted(dependencies))


def analyze_android_mobile_ads(
    manifest_text: str,
    *,
    gradle_texts: Iterable[str] = (),
) -> AndroidMobileAdsEvidence:
    application_id, permissions, delay_measurement = parse_android_manifest(manifest_text)
    dependencies: set[tuple[str, str]] = set()
    for gradle_text in gradle_texts:
        dependencies.update(parse_gradle_dependencies(gradle_text))
    return AndroidMobileAdsEvidence(
        application_id=application_id,
        permissions=permissions,
        sdk_dependencies=tuple(sorted(dependencies)),
        delay_app_measurement_init=delay_measurement,
    )


def load_android_mobile_ads(
    manifest_path: str | Path,
    *,
    gradle_paths: Iterable[str | Path] = (),
) -> AndroidMobileAdsEvidence:
    return analyze_android_mobile_ads(
        _bounded_text(manifest_path),
        gradle_texts=(_bounded_text(path) for path in gradle_paths),
    )


def parse_ios_info_plist(data: bytes) -> tuple[str | None, tuple[str, ...], bool | None, bool | None]:
    """Extract Google Mobile Ads keys from an XML or binary Info.plist."""
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if len(data) > _MAX_EVIDENCE_BYTES:
        raise MobileAdsEvidenceError("Info.plist evidence exceeds 16 MiB")
    try:
        payload = plistlib.loads(data)
    except Exception as exc:  # plistlib raises several concrete parse exceptions.
        raise MobileAdsEvidenceError("invalid Info.plist") from exc
    if not isinstance(payload, dict):
        raise MobileAdsEvidenceError("Info.plist root must be a dictionary")

    application_id = _validate_application_id(
        payload.get("GADApplicationIdentifier"), field="GADApplicationIdentifier"
    )

    raw_items = payload.get("SKAdNetworkItems", [])
    if not isinstance(raw_items, list):
        raise MobileAdsEvidenceError("SKAdNetworkItems must be an array")
    skad_ids: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise MobileAdsEvidenceError("SKAdNetworkItems entries must be dictionaries")
        identifier = item.get("SKAdNetworkIdentifier")
        if not isinstance(identifier, str) or not _SKAD_ID.fullmatch(identifier):
            raise MobileAdsEvidenceError("invalid SKAdNetworkIdentifier")
        skad_ids.append(identifier)

    delay = payload.get("GADDelayAppMeasurementInit")
    if delay is not None and not isinstance(delay, bool):
        raise MobileAdsEvidenceError("GADDelayAppMeasurementInit must be boolean")
    ad_manager = payload.get("GADIsAdManagerApp")
    if ad_manager is not None and not isinstance(ad_manager, bool):
        raise MobileAdsEvidenceError("GADIsAdManagerApp must be boolean")

    return application_id, tuple(sorted(set(skad_ids))), delay, ad_manager


def parse_podfile_lock(text: str) -> str | None:
    """Extract the resolved Google-Mobile-Ads-SDK CocoaPods version."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    versions = {match.group(1).strip() for match in _POD_ADS.finditer(text)}
    if len(versions) > 1:
        raise MobileAdsEvidenceError("Podfile.lock contains conflicting Google Mobile Ads versions")
    return next(iter(versions), None)


def analyze_ios_mobile_ads(
    info_plist_data: bytes,
    *,
    podfile_lock_text: str | None = None,
) -> IOSMobileAdsEvidence:
    application_id, skad_ids, delay, ad_manager = parse_ios_info_plist(info_plist_data)
    return IOSMobileAdsEvidence(
        application_id=application_id,
        sdk_version=parse_podfile_lock(podfile_lock_text) if podfile_lock_text is not None else None,
        skadnetwork_ids=skad_ids,
        delay_app_measurement_init=delay,
        is_ad_manager_app=ad_manager,
    )


def load_ios_mobile_ads(
    info_plist_path: str | Path,
    *,
    podfile_lock_path: str | Path | None = None,
) -> IOSMobileAdsEvidence:
    source = Path(info_plist_path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.stat().st_size > _MAX_EVIDENCE_BYTES:
        raise MobileAdsEvidenceError("Info.plist evidence exceeds 16 MiB")
    podfile_text = _bounded_text(podfile_lock_path) if podfile_lock_path is not None else None
    return analyze_ios_mobile_ads(source.read_bytes(), podfile_lock_text=podfile_text)

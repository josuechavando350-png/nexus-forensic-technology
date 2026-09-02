from __future__ import annotations

import plistlib
import tempfile
import unittest
from pathlib import Path

from packages.forensic_core.google_mobile_ads import (
    MobileAdsEvidenceError,
    analyze_android_mobile_ads,
    analyze_ios_mobile_ads,
    load_android_mobile_ads,
    load_ios_mobile_ads,
    parse_android_manifest,
    parse_gradle_dependencies,
    parse_ios_info_plist,
    parse_podfile_lock,
)


ANDROID_MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.app">
  <uses-permission android:name="android.permission.INTERNET" />
  <uses-permission android:name="com.google.android.gms.permission.AD_ID" />
  <application>
    <meta-data
      android:name="com.google.android.gms.ads.APPLICATION_ID"
      android:value="ca-app-pub-3940256099942544~3347511713" />
    <meta-data
      android:name="com.google.android.gms.ads.DELAY_APP_MEASUREMENT_INIT"
      android:value="true" />
  </application>
</manifest>
"""


class GoogleMobileAdsTests(unittest.TestCase):
    def test_android_manifest_extracts_real_mobile_ads_metadata(self) -> None:
        app_id, permissions, delay = parse_android_manifest(ANDROID_MANIFEST)
        self.assertEqual(app_id, "ca-app-pub-3940256099942544~3347511713")
        self.assertIn("android.permission.INTERNET", permissions)
        self.assertIn("com.google.android.gms.permission.AD_ID", permissions)
        self.assertTrue(delay)

    def test_gradle_dependency_parser_handles_full_and_lite_artifacts(self) -> None:
        dependencies = parse_gradle_dependencies(
            'implementation("com.google.android.gms:play-services-ads:24.5.0")\n'
            "implementation 'com.google.android.gms:play-services-ads-lite:24.5.0'\n"
        )
        self.assertEqual(
            dependencies,
            (("play-services-ads", "24.5.0"), ("play-services-ads-lite", "24.5.0")),
        )

    def test_android_combines_manifest_and_dependency_evidence(self) -> None:
        evidence = analyze_android_mobile_ads(
            ANDROID_MANIFEST,
            gradle_texts=['implementation("com.google.android.gms:play-services-ads:24.5.0")'],
        )
        self.assertEqual(evidence.application_id, "ca-app-pub-3940256099942544~3347511713")
        self.assertEqual(evidence.sdk_dependencies, (("play-services-ads", "24.5.0"),))
        self.assertTrue(evidence.delay_app_measurement_init)

    def test_android_rejects_invalid_app_id_duplicate_metadata_and_bad_boolean(self) -> None:
        with self.assertRaisesRegex(MobileAdsEvidenceError, "valid Google Mobile Ads"):
            parse_android_manifest(
                ANDROID_MANIFEST.replace(
                    "ca-app-pub-3940256099942544~3347511713", "not-an-app-id"
                )
            )
        duplicate = ANDROID_MANIFEST.replace(
            "</application>",
            '<meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" '
            'android:value="ca-app-pub-3940256099942544~3347511713" /></application>',
        )
        with self.assertRaisesRegex(MobileAdsEvidenceError, "duplicate"):
            parse_android_manifest(duplicate)
        with self.assertRaisesRegex(MobileAdsEvidenceError, "true or false"):
            parse_android_manifest(
                ANDROID_MANIFEST.replace('android:value="true"', 'android:value="yes"')
            )

    def test_android_rejects_malformed_xml(self) -> None:
        with self.assertRaisesRegex(MobileAdsEvidenceError, "invalid AndroidManifest"):
            parse_android_manifest("<manifest>")

    def test_ios_extracts_app_id_skadnetwork_and_flags(self) -> None:
        payload = plistlib.dumps(
            {
                "GADApplicationIdentifier": "ca-app-pub-3940256099942544~1458002511",
                "GADDelayAppMeasurementInit": False,
                "GADIsAdManagerApp": True,
                "SKAdNetworkItems": [
                    {"SKAdNetworkIdentifier": "cstr6suwn9.skadnetwork"},
                    {"SKAdNetworkIdentifier": "4fzdc2evr5.skadnetwork"},
                ],
            }
        )
        app_id, skad_ids, delay, ad_manager = parse_ios_info_plist(payload)
        self.assertEqual(app_id, "ca-app-pub-3940256099942544~1458002511")
        self.assertEqual(
            skad_ids,
            ("4fzdc2evr5.skadnetwork", "cstr6suwn9.skadnetwork"),
        )
        self.assertFalse(delay)
        self.assertTrue(ad_manager)

    def test_ios_podfile_lock_extracts_resolved_sdk_version(self) -> None:
        lock = """PODS:
  - Google-Mobile-Ads-SDK (12.8.0):
    - GoogleUserMessagingPlatform (>= 1.1)
DEPENDENCIES:
  - Google-Mobile-Ads-SDK
"""
        self.assertEqual(parse_podfile_lock(lock), "12.8.0")
        payload = plistlib.dumps(
            {"GADApplicationIdentifier": "ca-app-pub-3940256099942544~1458002511"}
        )
        evidence = analyze_ios_mobile_ads(payload, podfile_lock_text=lock)
        self.assertEqual(evidence.sdk_version, "12.8.0")

    def test_ios_rejects_invalid_structures_and_identifiers(self) -> None:
        with self.assertRaisesRegex(MobileAdsEvidenceError, "SKAdNetworkItems must be an array"):
            parse_ios_info_plist(plistlib.dumps({"SKAdNetworkItems": "wrong"}))
        with self.assertRaisesRegex(MobileAdsEvidenceError, "invalid SKAdNetworkIdentifier"):
            parse_ios_info_plist(
                plistlib.dumps(
                    {"SKAdNetworkItems": [{"SKAdNetworkIdentifier": "invalid"}]}
                )
            )
        with self.assertRaisesRegex(MobileAdsEvidenceError, "must be boolean"):
            parse_ios_info_plist(plistlib.dumps({"GADIsAdManagerApp": "true"}))

    def test_podfile_lock_rejects_conflicting_versions(self) -> None:
        with self.assertRaisesRegex(MobileAdsEvidenceError, "conflicting"):
            parse_podfile_lock(
                "- Google-Mobile-Ads-SDK (12.7.0)\n- Google-Mobile-Ads-SDK (12.8.0)\n"
            )

    def test_file_loaders_use_real_local_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "AndroidManifest.xml"
            gradle = root / "build.gradle.kts"
            plist = root / "Info.plist"
            lock = root / "Podfile.lock"
            manifest.write_text(ANDROID_MANIFEST, encoding="utf-8")
            gradle.write_text(
                'implementation("com.google.android.gms:play-services-ads:24.5.0")',
                encoding="utf-8",
            )
            plist.write_bytes(
                plistlib.dumps(
                    {"GADApplicationIdentifier": "ca-app-pub-3940256099942544~1458002511"}
                )
            )
            lock.write_text("- Google-Mobile-Ads-SDK (12.8.0)\n", encoding="utf-8")

            android = load_android_mobile_ads(manifest, gradle_paths=[gradle])
            ios = load_ios_mobile_ads(plist, podfile_lock_path=lock)

        self.assertEqual(android.sdk_dependencies, (("play-services-ads", "24.5.0"),))
        self.assertEqual(ios.sdk_version, "12.8.0")


if __name__ == "__main__":
    unittest.main()

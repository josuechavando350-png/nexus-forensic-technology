# Audit 023 — Google Mobile Ads SDK evidence integration

## Scope

Executable, read-only forensic inspection of Google Mobile Ads SDK configuration evidence from Android and iOS application projects/build artifacts. The module does not request ads, generate ad traffic, contact Google advertising services, collect advertising identifiers, or modify application configuration.

## Real inputs implemented

### Android

- `AndroidManifest.xml` parsing with the platform Android XML namespace.
- Google Mobile Ads application metadata key `com.google.android.gms.ads.APPLICATION_ID`.
- `com.google.android.gms.ads.DELAY_APP_MEASUREMENT_INIT` boolean metadata.
- Declared permissions, including evidence such as `com.google.android.gms.permission.AD_ID` when present.
- Direct resolved/pinned Gradle dependency coordinates for:
  - `com.google.android.gms:play-services-ads:<version>`
  - `com.google.android.gms:play-services-ads-lite:<version>`

### iOS

- XML and binary `Info.plist` via Python's real `plistlib` parser.
- `GADApplicationIdentifier`.
- `GADDelayAppMeasurementInit`.
- `GADIsAdManagerApp`.
- `SKAdNetworkItems` / `SKAdNetworkIdentifier` evidence.
- Resolved `Google-Mobile-Ads-SDK` version from CocoaPods `Podfile.lock`.

## Integrity and validation

- Google Mobile Ads application IDs must match the documented `ca-app-pub-<16 digits>~<10 digits>` application-ID form.
- Duplicate Android application-ID metadata fails closed.
- Duplicate Android delayed-measurement metadata fails closed.
- Android delayed-measurement values must be literal booleans (`true`/`false`).
- iOS delayed-measurement and Ad Manager flags must be plist booleans.
- SKAdNetwork identifiers must use the 10-character `.skadnetwork` identifier form.
- Conflicting resolved CocoaPods SDK versions fail closed.
- File-backed and direct evidence inputs are bounded to 16 MiB.
- Malformed Android XML and malformed plist evidence fail closed.
- Results use immutable dataclasses and deterministic sorted tuples.

## Deliberate boundaries

This integration reports configuration and dependency evidence only. It does not claim that the SDK initialized successfully at runtime, that an ad request succeeded, or that a publisher account is valid. It does not invent runtime telemetry where no device/app execution evidence exists.

Gradle version-catalog aliases and Swift Package Manager lockfiles are not inferred as direct Maven/CocoaPods evidence by this module. Unsupported dependency representations are left absent rather than guessed.

## Tests

`packages/forensic_core/tests/test_google_mobile_ads.py` covers:

- Android application-ID, permission, and delayed-measurement extraction.
- Full and lite Maven dependency extraction.
- Combined Android evidence construction.
- Invalid/duplicate Android metadata rejection.
- Malformed Android XML rejection.
- iOS application-ID, SKAdNetwork, and boolean flag extraction.
- CocoaPods resolved SDK-version extraction.
- Invalid plist structures and identifiers.
- Conflicting CocoaPods versions.
- Real file-backed Android and iOS evidence loaders.

## Certification rule

Do not merge until the final PR diff is reviewed and every repository pull-request check completes successfully.

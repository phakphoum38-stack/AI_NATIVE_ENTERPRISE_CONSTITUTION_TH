# Settings and Governance

## Purpose

Application settings are owned by `AppSettingsController` so UI components read one source of truth for theme, language, approval preference, and evidence retention.

## Current preferences

- Theme mode: system, light, or dark
- Language: system, Thai, or English
- High-risk approval preference
- Evidence retention preference

## Design boundary

The settings controller contains no provider SDK dependency. Provider selection and execution remain under the provider controller and orchestrator boundaries.

## Startup behavior

`AppDependencies.initialize()` connects the first registered provider before the
application UI is rendered. The default Local Demo Provider is therefore ready
for governed requests when the Assistant screen first opens.

## Evidence

Changes are covered by `test/app/app_settings_test.dart` and validated through the Flutter Quality workflow.

# AI Native Enterprise Constitution TH

โครงการ Flutter อ้างอิงสำหรับพัฒนาระบบ Enterprise แบบ AI-Native โดยใช้ Constitution ภาษาไทยเป็นแหล่งกติกาหลักเพียงชุดเดียว

## สถานะ

**Level 1 — Runnable Foundation MVP**

Foundation ปัจจุบันประกอบด้วย:

- Personal rights-holder license
- Provider-neutral AI request/response models
- AI Provider abstraction และ capability model
- Provider registry และ lifecycle controller
- Provider health check, recovery และ cancellation
- Local Demo Provider สำหรับการพัฒนาแบบไม่ใช้ API key
- เชื่อมต่อ Local Demo Provider อัตโนมัติก่อนแสดงแอป
- Privacy/risk execution policy
- Human approval gate
- Policy-aware AI orchestrator
- Evidence log สำหรับผลสำเร็จและความล้มเหลว
- Flutter Composition Root และ Provider dashboard
- Unit tests และ GitHub Actions quality gate

## หลักการสูงสุด

- Long-term First
- One Truth
- AI is a Team Member
- Every Change Has Evidence
- Documentation Never Lags Behind Code
- Quality Is Continuous
- Provider Independent

## โครงสร้าง

```text
.
├── .github/workflows/
│   └── quality.yml
├── docs/
│   ├── architecture/
│   └── governance/
├── lib/
│   ├── ai_engine/
│   │   ├── models/
│   │   ├── orchestration/
│   │   └── providers/
│   ├── app/
│   ├── core/
│   │   ├── evidence/
│   │   └── policy/
│   ├── screens/
│   └── main.dart
├── test/
│   ├── ai_engine/
│   └── core/
├── analysis_options.yaml
├── pubspec.yaml
├── LICENSE-PERSONAL.md
└── README.md
```

## Runtime flow

```text
User Request
→ AI Execution Context
→ Privacy and Risk Policy
→ Approval Gate
→ Active Provider
→ AI Response
→ Evidence Record
```

## Development flow

```text
Read Constitution
→ Inspect Repository
→ Design
→ Implement
→ Write Tests
→ Format
→ Analyze
→ Test
→ Review Diff
→ Pull Request
→ Human Approval
→ Merge
```

## Validation

GitHub Actions ดาวน์โหลด Flutter SDK 3.44.8 และรัน:

```bash
flutter --version
flutter doctor -v
flutter pub get
dart format --output=none --set-exit-if-changed .
flutter analyze
flutter test
```

จัดรูปแบบทุกไฟล์ Dart ด้วย:

```bash
dart run tool/format_all.dart
```

ตรวจรูปแบบโดยไม่แก้ไขไฟล์ด้วย:

```bash
dart run tool/format_all.dart --check
```

## Run and build

แอปเชื่อมต่อ Local Demo Provider โดยอัตโนมัติเมื่อเริ่มต้น จึงสามารถเปิดหน้า
Assistant และส่งข้อความได้ทันที

สร้าง release bundles สำหรับทุก platform ที่รองรับบน environment นี้ด้วย:

```bash
flutter build apk --release
flutter build web --release --no-wasm-dry-run
flutter build linux
```

ผลลัพธ์จะอยู่ที่:

```text
build/app/outputs/flutter-apk/app-release.apk
build/web/
build/linux/x64/release/bundle/ai_native_enterprise_constitution
```

## Provider boundary

Core และ UI ห้ามผูกกับ SDK ของผู้ให้บริการรายใดโดยตรง Provider จริงต้องเพิ่มผ่าน `AiProvider` adapter และต้องผ่าน Policy, Privacy, Approval และ Evidence flow เดียวกัน

## License

Copyright © 2026 Phakphum Wiriyaphap. All rights reserved.

เงื่อนไขการใช้งาน การอนุญาต ข้อยกเว้น การตีความ และสิทธิ์เพิ่มเติมทั้งหมดเป็นไปตามที่เจ้าของสิทธิ์กำหนดและอนุมัติเป็นลายลักษณ์อักษรเท่านั้น โปรดดู `LICENSE-PERSONAL.md`

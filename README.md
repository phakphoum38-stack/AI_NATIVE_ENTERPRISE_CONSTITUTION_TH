# AI Native Enterprise Constitution TH

โครงการอ้างอิงสำหรับพัฒนาระบบ Enterprise แบบ AI-Native โดยยึด Constitution ภาษาไทยเป็นแหล่งกติกาหลักเพียงชุดเดียว

## สถานะ

**Level 1 — Prototype / Foundation**

โครงสร้างเริ่มต้นประกอบด้วย:

- Enterprise และ AI-Native Constitution
- Personal rights-holder license
- AI Provider abstraction
- AI Provider registry
- AI Provider controller
- Unit tests สำหรับ provider foundation

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
├── docs/
│   ├── governance/
│   └── architecture/
├── lib/
│   └── ai_engine/
│       └── providers/
├── test/
│   └── ai_engine/
│       └── providers/
├── analysis_options.yaml
├── pubspec.yaml
├── LICENSE-PERSONAL.md
└── README.md
```

## Development flow

```text
Read Constitution
→ Inspect Repository
→ Design
→ Implement
→ Format
→ Analyze
→ Test
→ Review Diff
→ Pull Request
→ Human Approval
→ Merge
```

## Validation

```bash
flutter pub get
dart format --output=none --set-exit-if-changed .
flutter analyze
flutter test
```

## License

Copyright © 2026 Phakphum Wiriyaphap. All rights reserved.

เงื่อนไขการใช้งาน การอนุญาต ข้อยกเว้น การตีความ และสิทธิ์เพิ่มเติมทั้งหมดเป็นไปตามที่เจ้าของสิทธิ์กำหนดและอนุมัติเป็นลายลักษณ์อักษรเท่านั้น โปรดดู `LICENSE-PERSONAL.md`.

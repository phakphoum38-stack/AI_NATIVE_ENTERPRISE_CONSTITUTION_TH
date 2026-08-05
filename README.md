# AI Workspaces Model

แพลตฟอร์ม AI-Native Enterprise สำหรับจัดการ Workspace, Repository, Branch, Commit, Pull Request, Review, Workflow, AI Provider และ Audit ภายใต้ Constitution และ Human Approval เดียวกัน

## สถานะ

**Version 1 — Governed Workspace Foundation**

ระบบหลักประกอบด้วย:

- Flutter application สำหรับ AI orchestration, provider lifecycle และ human approval
- FastAPI backend พร้อม SQLite persistence
- Repository, branch, commit และ pull request APIs
- Review scorecard และ merge governance gates
- Workflow run tracking
- AI provider abstraction และ explainable response trace
- Audit log
- Web dashboard
- Docker และ Docker Compose
- GitHub Actions สำหรับ Flutter, Backend, Documentation และ Security

## โครงสร้าง

```text
.
├── backend/                  # FastAPI API และ tests
├── frontend/                 # Web dashboard แบบเบา
├── lib/                      # Flutter AI-native application
├── test/                     # Flutter tests
├── docs/
│   ├── architecture/
│   ├── constitution/
│   └── governance/
├── .github/workflows/
├── Dockerfile
├── docker-compose.yml
├── pubspec.yaml
└── README.md
```

## Run Flutter

```bash
flutter pub get
flutter analyze
flutter test
flutter run
```

## Run Backend

```bash
cd backend
python -m venv .venv
python -m pip install -r requirements.txt
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. uvicorn app.main:app --reload
```

บน PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "."
python -m pytest -q
python -m uvicorn app.main:app --reload
```

## Run with Docker

```bash
docker compose up --build
```

Backend จะเปิดที่ `http://localhost:8000` และ OpenAPI อยู่ที่ `/docs`

## Governance flow

```text
User Request
→ Constitution and Policy
→ Human Approval Gate
→ Workspace / Repository Operation
→ Tests and Workflow Evidence
→ Review Scorecard
→ Merge Gate
→ Audit Record
```

## หลักการสูงสุด

- Long-term First
- One Truth
- AI is a Team Member
- Every Change Has Evidence
- Documentation Never Lags Behind Code
- Quality Is Continuous
- Build for the next developer — whether human or AI

## License

Copyright © 2026 Phakphum Wiriyaphap. All rights reserved.

ดูเงื่อนไขเพิ่มเติมใน `LICENSE-PERSONAL.md`

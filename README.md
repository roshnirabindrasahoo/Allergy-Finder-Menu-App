# Allergy-Friendly Menu Finder

Full-stack web app:
- Frontend: Next.js (App Router)
- Backend: FastAPI (Python)
- DB: PostgreSQL
- Auth: JWT
- Ingestion: CSV/PDF (best-effort)
- AI/ML: keyword+fuzzy allergen suggestions

## Run (dev)

### 1) Backend
```bash
cd backend
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows
# .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env -> SECRET_KEY + DATABASE_URL (postgres) or use sqlite fallback
uvicorn app.main:app --reload --port 4000

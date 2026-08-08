# MarketIntellgence 

Lightweight full-stack finance analysis app (backend in Python, frontend in Vue.js).

## Overview
- Backend: API and analysis tools under `backend/`.
- Frontend: Vue.js single-page app under `frontend/`.

## Requirements
- Python 3.10+ for backend
- Node.js 16+ and npm/yarn for frontend

## Backend — Quick start
1. cd backend
2. python -m venv venv
3. source venv/bin/activate
4. pip install -r requirements.txt
5. Initialize DB (if needed):
   - `python init_db.py` or `python create_initial_data.py`
6. Run the API: `python main.py`

Notes:
- SQLite DB file: `backend/applications/instance/finance_app.sqlite3`
- Tests: `python test.py` and `python test_api.py` (run from `backend/`).

## Frontend — Quick start
1. cd frontend
2. npm install
3. npm run serve
4. Open the app at `http://localhost:8080` (or the port reported by the dev server)

## Project structure (high level)
- `backend/` — Python APIs, data models, analysis modules (see `backend/applications/`).
- `frontend/` — Vue source in `src/`, views in `views/`, components in `components/`.

## Contributing
- Open issues or PRs for bugs, improvements, or documentation updates.

## Contact
If you want changes to this README or to add usage examples, tell me what to include.

## License
MIT (placeholder) — replace with the project's chosen license.

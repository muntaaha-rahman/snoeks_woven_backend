# Snoeks Wonen - measurement app (backend)

FastAPI backend for recording on-site measurements (window treatments,
flooring, insect screens, sun shading) taken at customers' homes, storing
them in a shared database, and automatically emailing a PDF report to
info@snoekswonen.nl on every save.

Pairs with the [frontend PWA](../snoeks_woven_frontend).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # includes runtime deps + test tools
cp .env.example .env   # fill in SMTP credentials
.venv/bin/uvicorn app.main:app --reload
```

Uses SQLite by default (zero setup). For production, set `DATABASE_URL` to a
Postgres connection string in `.env`.

## Tests

```bash
.venv/bin/pytest
```

## Docker

```bash
docker build -t snoeks-woven-backend .
docker run -p 8420:8000 \
  -v snoeks_uploads:/app/uploads -v snoeks_data:/app/data \
  --env-file .env \
  snoeks-woven-backend
```

Or run both services together via `docker-compose.yml` one level up (see the
repo root). Port 8420 (not 8000) is used there to avoid clashing with other
projects on the same machine.

## Structure

- `app/models.py` / `app/schemas.py` - the data model: a Visit has many Rooms,
  each with window treatments, flooring sections, insect screens, and sun
  shading items, each of which can carry photos.
- `app/crud.py` - persistence, including saving inline base64 photos captured
  on-device at creation time.
- `app/pdf.py` + `app/templates/report.html` - renders the PDF report via
  WeasyPrint.
- `app/email_utils.py` - sends the report by SMTP; failures are recorded on
  the visit (`email_sent` / `email_error`) so the frontend can show a retry
  option rather than silently failing.
- `app/routers/` - the API endpoints.

## Known limitations

- No authentication - built for use on a trusted internal network/devices,
  since the spec didn't call for logins. Straightforward to add later.
- Editing a visit (`PUT /visits/{id}`) replaces its entire room tree, so any
  previously attached photos on that visit's items are orphaned. Fine for
  correcting typos in customer details; re-attach photos if you edit rooms.

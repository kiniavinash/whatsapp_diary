# WhatsApp Diary (Export-based MVP)

A local web app to import exported WhatsApp chat text files and ask questions over your notes via search/RAG.

## Setup with uv

1) Install uv (one-time):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/home/avinash/.local/bin:/home/avinash/.nvm/versions/node/v22.19.0/bin:/usr/bin:/usr/local/cuda/bin:/tmp/.mount_CursorUnDHPg/usr/bin/:/tmp/.mount_CursorUnDHPg/usr/sbin/:/tmp/.mount_CursorUnDHPg/usr/games/:/tmp/.mount_CursorUnDHPg/bin/:/tmp/.mount_CursorUnDHPg/sbin/:/home/avinash/.nvm/versions/node/v22.19.0/bin:/usr/bin:/usr/local/cuda/bin:/home/avinash/miniforge-pypy3/condabin:/home/avinash/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin:/snap/bin"
```

2) Sync deps and create a virtual env:

```bash
uv sync
```

3) Run the dev server:

```bash
uv run uvicorn app.main:app --reload
```

4) Run tests:

```bash
uv run pytest -q
```

## Export chat (manual)

- Android: Chat > ⋮ > More > Export Chat > Without media > Save to a fixed folder (e.g., `Downloads/WhatsAppExports`).
- iOS: Chat > Contact name > Export Chat > Without Media > Save to Files (iCloud/On My iPhone) in a fixed folder.

Then upload the  via the UI, or place it into  and use the  endpoint.

## Project layout

- `app/main.py` — FastAPI app, routes, static files
- `app/services/parser.py` — WhatsApp  parser
- `app/services/db.py` — SQLite (SQLAlchemy) models and session
- `app/services/importer.py` — incremental importer & dedup
- `static/index.html` — minimal Tailwind UI

## Notes

- By default, data is stored in `data/db.sqlite3`.
- Embeddings/RAG for `/ask` will be added next.

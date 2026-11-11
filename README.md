# Folio — Ajaia AI-Native Full Stack Developer Assignment

A deliberately scoped, collaborative rich-text document editor. One small FastAPI application serves a browser UI and REST API, with SQLite locally and optional PostgreSQL for durable cloud deployment.

## Features

- Create, rename, edit, autosave, and reopen documents
- Bold, italic, underline, H1/H2, paragraphs, bulleted and numbered lists
- Import **UTF-8 `.txt` and `.md` files up to 512 KB** into editable documents
- Switch among three seeded demo identities; grant and revoke editor access
- Explicit **My documents** and **Shared with me** libraries
- Persist sanitized HTML and sharing data in SQLite (or PostgreSQL)
- Client feedback, server validation, user authorization checks, and automated tests

## Local setup

Requires **Python 3.10+**.

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000**. Database file `ajaia.db` is created on first run. To run tests:

```bash
pytest -q
```

### Demo users

| Demo identity | Email | Use |
| --- | --- | --- |
| Alex Morgan | alex@demo.test | Create and own a document |
| Jordan Lee | jordan@demo.test | Receive a share and edit it |
| Sam Rivera | sam@demo.test | Additional collaborator |

Use the **Viewing as** selector in the sidebar. No password is needed. **This is intentionally mocked authentication; an HTTP header is not proof of identity. Do not put real or confidential documents in this demo.**

## Reviewer walkthrough

1. Select Alex and click **Create document**; rename it.
2. Write a paragraph; select text and use **B**, **I**, **U**, **H1/H2**, or lists. Watch the autosave indicator.
3. Return to My documents and reopen to see persisted formatting.
4. Click **Share**, select Jordan, and grant access.
5. Switch to Jordan, click **Shared with me**, open and edit Alex's document.
6. Switch back to Alex and see Jordan's changes. Revoke Jordan in the Share modal; Jordan loses access.
7. Import a `.txt` or `.md` document using the link in the library.

## Deploy to Render + PostgreSQL

1. Push this project to your own GitHub repository.
2. In Render, create a **Postgres** database (free option if available). Copy its **internal database URL**. Note that the Render free Postgres tier is **temporary and expires after 30 days**; check the current tier policy before submitting.
3. In Render, create a Python **Web Service** from that repository. Use build command `pip install -r requirements.txt` and start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. In the web service's **Environment**, set `DATABASE_URL` to the Postgres connection URL. Deploy.
5. Visit the generated `.onrender.com` URL, perform the reviewer walkthrough, and test after a reload.

A `render.yaml` blueprint is provided, but **the PostgreSQL `DATABASE_URL` must be configured**. Do not use the default SQLite database on a Render Free web service for the review deployment: its filesystem is ephemeral and **data can disappear during spin-down or restart**. Render's free service may also take time to wake on its first request.

## API overview

| Route | Purpose |
| --- | --- |
| `GET /api/users` | Demo identities |
| `GET /api/documents` | Owned/shared document lists |
| `POST /api/documents` | Create document |
| `GET /api/documents/{id}` | Read accessible document |
| `PATCH /api/documents/{id}` | Update title and sanitized content |
| `POST /api/documents/{id}/share` | Owner grants editor access |
| `DELETE /api/documents/{id}/share/{user_id}` | Owner revokes access |
| `POST /api/import` | Import text/Markdown as new document |
| `GET /api/health` | Deployment health check |

All document endpoints require `X-User-ID`, intentionally used as demo-only identity. The API enforces access for each document operation; share/revoke is owner-only. The user selector is not secure authentication.

## Scope and limitations

- Collaboration is asynchronous: one editor saves, then another reopens/reloads. **Not Google Docs-style real-time co-editing.** Concurrent writes are last-write-wins.
- Rich-text toolbar uses browser `document.execCommand` for a compact zero-build implementation. This older API is deprecated; a production editor would use TipTap/ProseMirror and schema-based content.
- No production login, invitations by email, audit log, automated version history, or offline editing.
- Basic HTML sanitization and upload validation; production would require more extensive security review, stricter auth, and rate limits.
- `DATABASE_URL` supports a SQLAlchemy-compatible SQLite or PostgreSQL URL. For Postgres `postgresql://...` is normalized to the psycopg driver.

## Architecture and AI use

See [ARCHITECTURE.md](ARCHITECTURE.md), [AI_WORKFLOW.md](AI_WORKFLOW.md), and [SUBMISSION.md](SUBMISSION.md).

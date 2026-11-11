# Architecture decisions

## Product slice

I prioritized one reliable journey: **create → format → autosave → share → switch user → edit → reopen**. A clean document library and import flow make that journey discoverable. The goal is to show coherent product behavior, not a feature-count contest.

## System

- **Frontend:** Responsive HTML/CSS and small vanilla JS state manager; browser `contenteditable` and formatting toolbar. Autosaves after ~650 ms of inactivity, displays saving/errors, and flushes on navigation.
- **Backend:** FastAPI REST API with Pydantic validation, per-request authorization, and sanitized stored HTML.
- **Database:** SQLAlchemy models for `User`, `Document`, and `Share`, SQLite locally; PostgreSQL URL supported in hosted environments.
- **Sharing:** Document ownership plus a unique document/user join table. Shared users can edit. Only the owner can grant or revoke access. Server checks authorization, not merely frontend buttons.
- **Import:** Reads bounded UTF-8 `.txt` and `.md` uploads; converts to HTML and applies the same sanitization path.
- **Tests:** API-level integration coverage of permissions, sharing, content sanitization, imports, and validation.

## Chosen tradeoffs

- **Simulated users vs auth:** A selector gives reviewers a complete sharing demo without account setup; it is explicitly not secure authentication.
- **Server storage vs localStorage:** Storage on the server proves refresh persistence and sharing between users.
- **HTML vs editor JSON:** Sanitized HTML preserves basic formatting and keeps the editor simpler for this exercise. Complex document schemas would favor ProseMirror JSON.
- **No WebSockets:** Real-time operational transforms/CRDTs would absorb time and introduce race/conflict cases before core flows are verified.
- **One app deployment:** Serving static assets and API together avoids CORS and multiple independently deployed services.

## Known risks and next 2–4 hours

1. Replace simulated identity with an authentication provider and verified server-side sessions.
2. Move editing to TipTap/ProseMirror to avoid deprecated `execCommand` and enforce a structured editing schema.
3. Add optimistic version columns and conflict detection, preventing accidental last-write-wins overwrites.
4. Add Playwright browser tests and deployment smoke checks.

Real-time multi-cursor collaboration would be a separate effort after those foundations.

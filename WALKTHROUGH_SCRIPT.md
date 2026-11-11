# 3–5 minute walkthrough script

> Record your own screen and voice, using actual tested behavior. Do not read any claims that you have not verified.

**0:00–0:25 — Product and framing**

“Hi, this is Folio, my submission for Ajaia's AI-Native Full Stack Developer assessment. I scoped it around one complete flow: create, edit, save, share, and reopen a document, rather than trying to recreate every Google Docs feature.”

**0:25–1:30 — Core editing experience**

“I'm viewing the workspace as Alex. I'll create a document, change its name, add formatted content, a heading, and a list. Changes save automatically. Now I'll navigate back and reopen it to show the title and rich text persist.”

**1:30–2:15 — Import and sharing**

“Import accepts UTF-8 text or Markdown files up to 512 KB. I'll import this Markdown note, which becomes an editable document. I'll now share the document with Jordan, one of the seeded demo users.”

**2:15–3:00 — Access controls**

“Switching to Jordan, I can find this item under Shared with me, open it, and edit it. The owner, Alex, can see the changes. Only the owner can grant or revoke access. I'll revoke Jordan, and the document will no longer be accessible to Jordan.”

**3:00–3:50 — Architecture, scope and test evidence**

“The app uses FastAPI and SQLAlchemy. Locally it stores documents in SQLite; for deployment it supports PostgreSQL so data can survive restarts. I store sanitized HTML for rich text, with server-side permission checks for every document operation. My automated integration tests cover access enforcement, sharing, import validation, and sanitization. I intentionally skipped real-time multi-cursor editing and secure user login: the demo identity selector is for quickly evaluating the access model, not production authentication.”

**3:50–4:20 — AI workflow and next steps**

“I used ChatGPT to accelerate the first pass of backend routes, UI interaction code, and integration tests. I reviewed and simplified the scope, corrected dependency issues, and verified the backend tests. With 2–4 more hours, I'd replace the simple editor with TipTap and implement real authentication and conflict detection.”

## Before recording

- Have a `.md` file ready for import (see `example-import.md`).
- Start with a cleanly loaded application and test the exact steps once.
- Show tests running in a terminal if time allows.
- Verify the live URL still works after refresh; ensure your database URL is configured.
- Publish as unlisted (accessible with link) and put the URL in `WALKTHROUGH_VIDEO_URL.txt` and `SUBMISSION.md`.

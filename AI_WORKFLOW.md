# AI workflow note — review and personalize before submitting

**Tool:** ChatGPT (GPT-6) assisted with the initial implementation draft, API/model design, frontend interactions, documentation, and test coverage.

**Where AI sped up work:** Generated the baseline FastAPI routes, SQLAlchemy models, compact UI components, upload validation, and integration test cases. This let the implementation focus on a coherent end-to-end flow.

**Decisions and changes:** The architecture deliberately avoids a complex real-time editor and opts for seeded users plus server-side permission checks. I also selected optional PostgreSQL for a hosted deployment, because an ephemeral SQLite file on free hosting would misrepresent persistence. Markdown parsing was changed to the available `mistune` library for local verification.

**Verification performed on the initial draft:** `python -m pytest -q` passed 3 integration tests; `node --check static/app.js` passed syntax checking; local HTTP smoke checks of `/`, `/app.js`, `/style.css`, and `/api/health` returned HTTP 200. These do not substitute for interactive browser testing.

**Verification to complete before submission:** Manually verify document save/reopen, formatting persistence, owner-only sharing, access revocation, both imports, mobile layout, and the deployed flow with two user identities. Include any actual bugs fixed or AI-generated suggestions rejected after hands-on review.

**Authorship and responsibility:** AI provided implementation assistance; I am responsible for reviewing, testing, understanding, and maintaining the delivered result. Do not claim browser or deployment tests were performed unless you completed them.

# api/ — Week 6 spine (unchanged)

This is the FastAPI + Docker + JWT triage service carried over as-is from
the Week 6 capstone (`afyaplus-service-platform`): `POST /triage` wraps a
real `gpt-4o-mini` call behind role-gated JWT auth, `POST /ask-logistics`
runs a LangChain/MCP agent over clinic logistics tools, and everything is
containerised in `Dockerfile`.

Week 7 does not touch this code. The cost, deploy, levers, memo, and exec
work in the repo root treats this service as the workload being costed
and optimised — see the top-level `README.md` for how the pieces fit
together.

Run it locally:

```
pip install -r requirements-api.txt
cp .env.example .env   # fill in JWT_SECRET / OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Run the offline test suite (no network calls, no API key needed):

```
pip install -r requirements.txt
pytest tests/ -q
```

**Known test status (unrelated to Week 7 scope):** 21/23 pass as of
2026-09-17. The 2 failures (`test_triage_without_token_is_401`,
`test_ask_logistics_without_token_is_401`) expect a missing
`Authorization` header to return 401; with `fastapi==0.115.14` installed
unpinned in this environment, FastAPI's `HTTPBearer` returns 403 in that
case instead. This is a version-drift artifact of `requirements-api.txt`
not pinning exact versions, inherited unchanged from the Week 6 spine —
not touched here, since Week 7 grades cost/economics work, not JWT
internals (see the capstone brief: "not redesigning JWT from scratch").
Pin `fastapi` to the version used when the Week 6 tests last passed if
this needs to be exact.

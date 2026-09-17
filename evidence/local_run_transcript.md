# Local run evidence — Deliverable 2

Real terminal output from `deploy/docker-compose.cost.yml`, captured
2026-09-17. Not a cloud console screenshot (no paid cloud account — see
`../deploy/budget_alert_notes.md` for the declared fallback), but a real
build and run against a local Docker Desktop engine, not a stub.

## Build + start

```
$ docker compose -f docker-compose.cost.yml up --build -d
...
 Image afyaplus-triage:cost-optimised Built
 Network deploy_default Created
 Container deploy-triage-api-1 Created
 Container deploy-triage-api-1 Started
```

## Container status

```
$ docker compose -f docker-compose.cost.yml ps
NAME                  IMAGE                            COMMAND                  SERVICE      CREATED         STATUS                   PORTS
deploy-triage-api-1   afyaplus-triage:cost-optimised   "uvicorn app.main:ap…"   triage-api   3 minutes ago   Up 3 minutes (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

## Health check

```
$ curl -s http://localhost:8000/health
{"service":"afyaplus-service-platform","version":"1.0.0","status":"ok"}
```

## FinOps tags, read back from the running container

```
$ docker inspect --format '{{json .Config.Labels}}' deploy-triage-api-1
{
  "finops.budget-ceiling-usd-month": "20",
  "finops.cost-center": "afyaplus-clinical-ops",
  "finops.environment": "capstone-week7",
  "finops.owner": "pmutua@live.com",
  "finops.workload": "triage-api",
  ...(docker compose's own bookkeeping labels omitted)
}
```

All five `finops.*` tags declared in `docker-compose.cost.yml` are present
on the running container — the same tag vocabulary the budget configs in
`../deploy/azure_budget_triage.json` and `../deploy/aws_budget.json`
filter on (`cost-center: afyaplus-clinical-ops`).

Cache MISS/HIT and hit-rate-challenge transcripts are in
`../levers/measurements.md`.

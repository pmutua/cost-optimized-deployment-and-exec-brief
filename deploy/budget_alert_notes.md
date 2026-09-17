# Budget alerts — fallback declaration and evidence

## Fallback declared

**No paid cloud account** was available in this environment. Per the
capstone brief's fallback path ("No paid cloud account: submit local
Docker Compose + written Azure/AWS budget alert YAML/JSON configs and
screenshots from free-tier consoles or mentor accounts, architecture
marks still apply"), this repo submits:

- `azure_budget_triage.json` / `aws_budget.json` — config-as-code, valid
  and ready to apply, but never actually applied against a live
  subscription/account.
- Local Docker Compose run evidence in place of a cloud console
  screenshot (below).

## What the configs do

Both configs set a **$20/month** ceiling scoped to the triage API via the
`cost-center: afyaplus-clinical-ops` tag (the same tag set as a label in
`docker-compose.cost.yml`), with two alert thresholds:

- **80% of actual spend** — early warning, still inside budget.
- **100% of forecasted spend** — the account is on track to exceed budget
  this cycle even if it hasn't yet, giving time to act before an overage
  actually posts.

Both notify `pmutua@live.com` by email. $20/month is the *production*
ceiling for the always-on deployment modelled in `../cost/cost_model.py`
(1 instance = $15/month infra, footnote [4]) — separate from, and larger
than, this capstone's own **$5 soft experimentation cap** stated in the
brief and tracked in the top-level README.

## How these would be applied against a real account

Azure (requires `az login` and an active subscription):

```bash
az consumption budget create \
  --budget-name afyaplus-triage-monthly \
  --resource-group <your-resource-group> \
  --amount 20 \
  --time-grain Monthly \
  --start-date 2026-09-01 \
  --end-date 2027-09-01 \
  --category Cost
# then PATCH the notifications/filter blocks from azure_budget_triage.json
# via `az rest` or the portal, since the CLI's own budget-create flags
# don't cover tag filters or multi-threshold notifications in one call.
```

AWS (requires configured credentials and an account ID):

```bash
aws budgets create-budget \
  --account-id <your-account-id> \
  --budget file://aws_budget.json \
  --notifications-with-subscribers file://aws_budget.json
# (the file bundles both top-level keys; a real invocation would split
# it into Budget.json and Notifications.json, or extract each key with jq)
```

## Local run evidence (what was actually executed)

```
$ docker compose -f docker-compose.cost.yml up --build -d
$ docker compose -f docker-compose.cost.yml ps
$ curl -s http://localhost:8000/health
{"service":"afyaplus-service-platform","version":"1.0.0","status":"ok"}
$ docker inspect --format '{{json .Config.Labels}}' <container_id>
{"finops.budget-ceiling-usd-month":"20","finops.cost-center":"afyaplus-clinical-ops","finops.environment":"capstone-week7","finops.owner":"pmutua@live.com","finops.workload":"triage-api", ...}
```

Full transcript: see `../evidence/local_run_transcript.md`.

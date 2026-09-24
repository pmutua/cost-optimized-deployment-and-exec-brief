# Screenshot evidence

Terminal captures proving each command in the shot list (`SHOT_LIST.md`)
was actually run, not just described. GitHub-page evidence (repo,
branches, tags, network graph) was scoped out of this round — everything
below is a local command run against this machine's own Docker engine
and Python interpreter.

## Deliverable 1 — cost model

`python cost_model.py` and `python sensitivity.py`, run from `cost/`.

![cost model output](d1-01-cost-model-output.png)
![sensitivity output](d1-02-sensitivity-output.png)

## Deliverable 2 — deploy & budgets

`docker compose -f docker-compose.cost.yml up --build -d`, `ps`, a
health check, and the FinOps labels on the running container — run from
`deploy/`.

![compose up](d2-01-compose-up.png)
![compose ps](d2-02-compose-ps.png)
![health check](d2-03-health-check.png)
![FinOps labels](d2-04-finops-labels.png)

## Deliverable 3 — levers

`python cache_triage.py`, `python cache_hitrate.py`, and
`python batch_worker.py`, run from `levers/`.

![cache miss/hit](d3-01-cache-miss-hit.png)
![cache hit-rate report](d3-02-cache-hitrate-report.png)
![batch worker report](d3-03-batch-worker-report.png)

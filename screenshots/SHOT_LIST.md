# Screenshot shot list

Run each command below in a terminal at the repo root (or the folder
noted), capture the terminal window with **Win+Shift+S** (Windows Snipping
Tool), and save the PNG into `screenshots/` using the **exact filename**
listed. Once all files exist, tell me and I'll write the index and commit
them through the usual feature-branch flow.

## Deliverable 1 — cost model

| Filename | Command | Run from |
|---|---|---|
| `d1-01-cost-model-output.png` | `python cost_model.py` | `cost/` |
| `d1-02-sensitivity-output.png` | `python sensitivity.py` | `cost/` |

## Deliverable 2 — deploy & budgets

| Filename | Command | Run from |
|---|---|---|
| `d2-01-compose-up.png` | `docker compose -f docker-compose.cost.yml up --build -d` | `deploy/` |
| `d2-02-compose-ps.png` | `docker compose -f docker-compose.cost.yml ps` | `deploy/` |
| `d2-03-health-check.png` | `curl http://localhost:8000/health` | anywhere |
| `d2-04-finops-labels.png` | `docker inspect --format '{{json .Config.Labels}}' deploy-triage-api-1` | anywhere |

Tip: `cp ../api/.env.example ../api/.env` first if `.env` doesn't exist
yet — dev defaults are enough for this smoke test, no real key needed.

## Deliverable 3 — levers

| Filename | Command | Run from |
|---|---|---|
| `d3-01-cache-miss-hit.png` | `python cache_triage.py` | `levers/` |
| `d3-02-cache-hitrate-report.png` | `python cache_hitrate.py` | `levers/` |
| `d3-03-batch-worker-report.png` | `python batch_worker.py` | `levers/` |

## Deliverable 5 — GitHub evidence (gitflow + release) — SKIPPED

Scoped out of this round; not captured.

| Filename | What to capture |
|---|---|
| `d5-01-github-repo.png` | Repo main page — shows the **Private** badge and description |
| `d5-02-github-branches.png` | Branches dropdown — shows `main` and `develop` |
| `d5-03-github-tags.png` | Tags page — shows `v1.0.0`, `v1.1.0`, `v1.1.1` |
| `d5-04-github-network-graph.png` | Insights → Network graph — shows the merge structure (feature branches merging into develop, develop into main) |

Repo: https://github.com/pmutua/cost-optimized-deployment-and-exec-brief

## When you're done

Save all files above into this `screenshots/` folder with those exact
names, then let me know — I'll add a `screenshots/README.md` index (like
your Week 6 repo's), link it from the top-level README, and commit it on
a `feature/screenshots-evidence` branch through the same merge flow.

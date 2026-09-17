# Contributing to cost-optimized-deployment-and-exec-brief

## Branching (gitflow)

- `main` — always releasable; every commit on `main` is tagged.
- `develop` — integration branch; feature branches merge here first.
- `feature/short-description` (e.g. `feature/optimisation-levers`), branched
  from `develop`. One feature (one capstone deliverable, in this repo),
  merged back into `develop` with `git merge --no-ff` so the branch's own
  history stays visible in the log instead of being squashed away.

A branch lives **one working day, two at the absolute outside**. If it's
still open on day three, either merge what exists behind a flag or split
the remaining work into its own branch — don't let it keep drifting from
`develop`.

When a deliverable is release-ready, `develop` is merged into `main` and
the release is tagged (see Versions/Releases below).

## Commits

Atomic: one commit is one complete, logically single change (e.g. "add the
cache lever" separate from "measure the cache lever's hit-rate"). A commit
should leave the repo in a working state — don't split a change so finely
that an intermediate commit is broken.

## Versions

Semantic versioning (`MAJOR.MINOR.PATCH`) describes the effect on **the
packet a marker reads**, not on internal code:

- **MAJOR** — a deliverable's headline numbers or recommendation changed
  in a way that invalidates a prior read (e.g. the go/no-go flips).
- **MINOR** — a new deliverable or lever is added alongside existing ones.
- **PATCH** — wording, formatting, or footnote fixes with no change to the
  numbers or recommendation.

## Releases

`v1.0.0` on `main` is the commit the capstone is submitted against. To see
the exact state of the packet at submission time:

```
git show v1.0.0
```

## When a merge conflict appears

1. Read both sides of every `<<<<<<<` / `=======` / `>>>>>>>` block and
   choose (or hand-merge) the correct lines — don't take "ours" or
   "theirs" wholesale without reading both.
2. Delete the conflict markers themselves.
3. Re-run the affected script (cost model, cache hit-rate, batch
   measurement) and confirm the numbers it prints still match what's
   written in the corresponding `.md` file before committing the
   resolution.

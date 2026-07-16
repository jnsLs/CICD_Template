# CI/CD Setup Guide (GitHub + Pixi + Python)

## 1. Branching & Protection Strategy

### Branch Model
- `main` → production (releases only)
- `dev` → integration branch (PR target)
- `feature/*` → feature branches
- Flow: feature → dev → main

> **Trunk-based alternative**: for small projects with one or two contributors, skip `dev` and target `main` directly (feature → main). The two-branch model only pays off when you need a staging integration point separate from production — e.g. multiple in-flight features that have to integrate before release. Otherwise the extra branch is just review/merge overhead.

### Branch Protection Rules
Apply rules to **`main`** and **`dev`** via repo settings → branches → add branch ruleset:
- Require pull requests (no direct pushes)
- Require status checks (tests, lint, etc.)
- Require branches to be up-to-date before merging
- Optionally require at least 1 review
- Do never rebase main on dev or feature branch
- **Restrict who can push** to `main` (only maintainers / specific roles) to enforce the feature → dev → main flow

> **Don't enforce branch flow in CI.** A CI job that fails when a PR to `main` doesn't come from `dev` looks like a guardrail but isn't one — anyone opening the PR can edit `.github/workflows/*.yml` in the same PR to disable the check. Use branch protection (push restrictions + required reviews from maintainers) instead. GitHub doesn't have a native "PR source must be branch X" rule, so the practical model is: lock down who can merge into `main`, and let convention + review handle the rest.

### Environments (TODO)
Use GitHub Environments:
- Define environments like `staging` and `production`
- Add:
  - Required approvers
  - Wait timers
- Useful for controlled deployments

---

## 2. GitHub Actions (CI/CD Workflows)

### Workflow Structure

Create workflows in: .github/workflows/

Recommended setup:
- `ci.yml` → runs on PRs (lint, test, checks)
- `release.yml` → handles publishing

---

### CI Workflow ([`integrate.yaml`](.github/workflows/integrate.yaml))
Runs on:
- Pushes to `main` and `dev`, and pull requests targeting them (plus manual `workflow_dispatch`)

Responsibilities:
- Install dependencies (via Pixi)
- Run linting
- Run tests
- Validate environment

#### Performance Tip: Caching
Use caching (e.g. `actions/cache` or Pixi caching) to speed up builds significantly.

#### Workflow Hygiene
Small additions that make workflows cheaper, safer, and easier to debug:
- **`concurrency` group**: cancel older runs on the same branch/PR when a new commit is pushed. Saves CI minutes and avoids stale "green checks" from outdated commits.
  ```yaml
  concurrency:
    group: ${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
  ```
- **`timeout-minutes` per job**: hard ceiling so a hung job doesn't burn the full 6-hour default.
  ```yaml
  jobs:
    tests:
      timeout-minutes: 15
  ```
- **Upload artifacts on failure**: keep test reports / logs so you can debug without re-running. Use `if: failure()` and `actions/upload-artifact`. Tip: have `pytest` write a JUnit XML (`pytest --junitxml=pytest-results.xml`) — no extra deps needed.
- **Coverage reporting**: `pytest-cov` is wired into the `test` pixi task (`pytest --cov=src --cov-report=term-missing`) so you see covered/uncovered lines locally. CI additionally writes `coverage.xml`, uploads it as a GitHub artifact, and pushes it to **Codecov** via `codecov/codecov-action@v5`. Codecov posts a comment on every PR with the coverage diff. Behavior is tuned in [`codecov.yml`](codecov.yml) (project threshold, patch coverage targets). To enforce a hard local minimum, add `--cov-fail-under=N` to the test task.
  - **One-time setup required**: sign in at [codecov.io](https://about.codecov.io/) with GitHub, add this repo, copy the upload token, and add it as `CODECOV_TOKEN` under repo settings → Secrets and variables → Actions.


### Precommits:
- `pip install pre-commit` or `pixi add pre-commit`
- create .pre-commit-config.yaml
- `pre-commit install`
- pre-commit only runs on staged files. otherwise use: pixi run pre-commit run --all-files

---

### Release Workflow (`release.yml`)

#### Trigger (IMPORTANT)
Trigger on **GitHub Releases**, not just tags. A minimal job skeleton using PyPI Trusted Publishers (no API token to store or rotate):

```yaml
name: Release

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi  # optional: gate on a GitHub Environment with required reviewers
    permissions:
      id-token: write  # REQUIRED for PyPI Trusted Publishers (OIDC)
      contents: read   # least privilege; we only need to checkout

    steps:
      - uses: actions/checkout@v4

      - name: Setup Pixi
        uses: prefix-dev/setup-pixi@v0.9.5
        with:
          cache: true
          frozen: true

      - name: Build distribution
        run: pixi run python -m build  # requires `build` in pixi deps

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # No `password:` — OIDC handles auth via the id-token permission.
```

The OIDC handshake requires both `id-token: write` in the workflow **and** a one-time Trusted Publisher entry on PyPI (Account → Publishing → Add a new publisher).

### Documentation (`docs.yml`)
Docs build/publish belongs in its own workflow, separate from release:
- **Tooling**: [MkDocs](https://www.mkdocs.org/) (Markdown-based, simple) or [Sphinx](https://www.sphinx-doc.org/) (richer, common in scientific Python).
- **Hosting**: [Read the Docs](https://readthedocs.org/) auto-builds on push to `main` once you connect the repo — no workflow file needed beyond webhook setup. Alternative: build in Actions and deploy to GitHub Pages.
- **Triggers**: on push to `main` (publish) and on PRs (build-only, to catch broken docs before merge).
- Keep sources in `docs/`.

## 3. GitHub Apps:
- CodeRabbit or Copilot for automatic PR reviews
  - Install the [CodeRabbit GitHub App](https://github.com/apps/coderabbitai) on the repo — the config file alone does nothing until the app is installed.
  - Behavior is tuned in [`.coderabbit.yaml`](.coderabbit.yaml): it auto-reviews PRs targeting `dev`/`main`, uses the less-nitpicky `chill` profile, and won't block merges (`request_changes_workflow: false`).
- Renovate or Dependabot to keep dependencies up to date
- Renovate has a dashboard and also creates an issue where you can see an overview of the detected dependencies and PRs in the pipeline
- You can set it up in the [`renovate.json`](renovate.json) file in the root directory of your repository
- It will repeatedly create PRs where it suggests updated workflow files, pyproject.toml files, …
- This repo's config **groups** all GitHub Actions bumps into one PR and **automerges** minor/patch + lockfile updates once CI is green (majors stay manual). Automerge only acts as a real gate when branch protection with required status checks is enabled.
- Avoid python version matrices because renovate cannot handle those
- After pyproject.toml is updated, one probably has to run pixi install again in order to update the lock file

## 4. Reproducibility with Pixi:
- Use pixi.toml, pyproject.toml and pixi.lock.
- pyproject.toml declares compatible ranges
- pixi.lock freezes exact versions (including transitive deps)
- Never change pixi.lock manually. Always use `pixi install`
- Can be automated in renovate.json
- One can specify tasks in pixi: for example the test task that can then be used by workflow files

## 5. References:
Pixi package management and programming environments:
- https://stackoverflow.com/questions/70851048/does-it-make-sense-to-use-conda-poetry
- https://jacobtomlinson.dev/posts/2025/python-package-managers-uv-vs-pixi/

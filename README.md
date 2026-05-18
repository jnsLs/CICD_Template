# CI/CD Setup Guide (GitHub + Pixi + Python)

## 1. Branching & Protection Strategy

### Branch Model
- `main` → production (releases only)
- `dev` → integration branch (PR target)
- `feature/*` → feature branches
- Flow: feature → dev → main

### Branch Protection Rules
Apply rules to **`main`** and **`dev`**:
- repo settings → branches → add branch ruleset
- Require pull requests (no direct pushes)
- Require status checks (tests, lint, etc.)
- Require branches to be up-to-date before merging
- Optionally require at least 1 review
- Require linear history (prevents messy merge commits) (only rebase and squash merges)

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

### CI Workflow (`ci.yml`)
Runs on:
#TODO: change this accordingly in the code
- Pull requests to `dev`

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
Trigger on **GitHub Releases**, not just tags:
```yaml
on:
  release:
    types: [published]
```

Responsibilities:
- build package
- publish to PyPI (or internal registry)
- use PyPI Trusted Publishers (OIDC) (Avoid storing API tokens)
- create hooks for documentation like read-the-docs
    - auto-build on push to main
    - use docs/ + mkdocs or sphinx

## 3. GitHub Apps:
- CodeRabit or Copilot for automatic PR reviews
- Renovate or Dependabot to keep dependencies up to date
- Renovate has a dashboard and also creates an issue where you can see an overview of the detected dependencies and PRs in the pipeline
- You can set it up in the renovate.json file in the root directory of your repository
- It will repeatedly create PRs where it suggests updated workflow files, pyproject.toml files, …
- Avoid python version matrices because renovate cannot handle those
- After pyproject.toml is updated, one probably has to run pixi install again in order to update the lock file

## 4. Reproducability with Pixi:
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

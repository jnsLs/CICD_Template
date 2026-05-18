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

### Environments (Optional but Recommended)
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


### Precommits:
- pip install pre-commit or pixi add pre-commit
- create .pre-commit-config.yaml
- pre-commit install
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
- Renovate or Dependabot to keep dependencies up to date.
- Renovate has a dashboard and also creates an issue where you can see an overview of the detected dependencies and PRs in the pipeline
- you can set it up in the renovate.json file in the root directory of your repository
- it will repeatedly create PRs where it suggests updated workflow files, pyproject.toml files, …
- avoid python version matrices because renovate cannot handle those
- after pyproject.toml is updated, one probably has to run pixi install again in order to update the lock file

## 4. Reproducability with Pixi:
- use pyproject.toml and pixi.lock.pyproject.toml declares compatible ranges
- pixi.lock freezes exact versions (including transitive deps)
- never change pixi.lock manually. always use pixi install
- can be automated in renovate.json see hello_world template repo
- one can specify tasks in pixi: for example the test task that can then be used by workflow files

## 5. References:
Pixi package management and programming environments:
- https://stackoverflow.com/questions/70851048/does-it-make-sense-to-use-conda-poetry
- https://jacobtomlinson.dev/posts/2025/python-package-managers-uv-vs-pixi/


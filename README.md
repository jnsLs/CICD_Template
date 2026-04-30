# CI/CD Setup Guide (GitHub + Pixi + Python)

## 1. Branching & Protection Strategy

### Branch Model
- `main` → production (releases only)
- `dev` → integration branch (PR target)
- `feature/*` → feature branches
- Flow: feature → dev → main

### Branch Protection Rules
Apply rules to **`main`** and **`dev`**:

- Require pull requests (no direct pushes)
- Require status checks (tests, lint, etc.)
- Require branches to be up-to-date before merging
- Optionally require at least 1 review
- Require linear history (prevents messy merge commits)

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
- Pull requests to `dev`

Responsibilities:
- Install dependencies (via Pixi)
- Run linting
- Run tests
- Validate environment

#### Performance Tip: Caching
Use caching (e.g. `actions/cache` or Pixi caching) to speed up builds significantly.

---

### Release Workflow (`release.yml`)

#### Trigger (IMPORTANT)
Trigger on **GitHub Releases**, not just tags:
```yaml
on:
  release:
    types: [published]

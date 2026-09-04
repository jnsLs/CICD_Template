# CI/CD Setup Guide (GitHub + Pixi + Python)
A reusable template for Python projects with Pixi, testing, linting, pre-commit hooks, GitHub Actions, coverage reporting, and automated dependency updates.

## 1. Branching & Protection Strategy

### Branch Model
- `main` → production (releases only)
- `dev` → integration branch (PR target)
- `feature/*` → feature branches
- Flow: feature → dev → main
- Never rebase main on dev or feature branch


### Branch Protection Rules
Apply rules to **`main`** and **`dev`** via repo settings → branches → add branch ruleset:
- Require pull requests (no direct pushes)
- Require status checks (tests, lint, etc.)
- Require branches to be up-to-date before merging
- Optionally require at least 1 review
- **Restrict who can push** to `main` (only maintainers / specific roles) to enforce the feature → dev → main flow


### (TODO) Environments
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

### CI Workflow ([`integrate.yml`](.github/workflows/integrate.yml))
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

- **Upload artifacts on failure**: keep test reports / logs so you can debug without re-running. Use `if: failure()` and `actions/upload-artifact`. Tip: have `pytest` write a JUnit XML (`pytest --junitxml=pytest-results.xml`) — no extra deps needed.
- **Coverage reporting**: `pytest-cov` shows covered/uncovered lines. Is part of the `test` pixi task (`pytest --cov=src --cov-report=term-missing`) which you can run locally. CI additionally writes `coverage.xml`, uploads it as a GitHub artifact, and pushes it to **Codecov** via `codecov/codecov-action@v5`. Codecov posts a comment on every PR with the coverage diff. Behavior is tuned in [`codecov.yml`](codecov.yml) (project threshold, patch coverage targets). To enforce a hard local minimum, add `--cov-fail-under=N` to the test task.
  - **One-time setup required**: sign in at [codecov.io](https://about.codecov.io/) with GitHub, add this repo, copy the upload token, and add it as `CODECOV_TOKEN` under repo settings → Secrets and variables → Actions.


### Precommits:
- `pip install pre-commit` or `pixi add pre-commit`
- create .pre-commit-config.yaml
- `pre-commit install`
- pre-commit only runs on staged files. otherwise use: pixi run pre-commit run --all-files

---

### Release Workflow ([`deploy.yml`](.github/workflows/deploy.yml))
Runs on: publishing a GitHub Release (`release: published`) — creating a tag alone does not trigger it.

#### Trusted Publisher on PyPI (one-time)
No `PYPI_API_TOKEN` needed — auth is OIDC, gated by `permissions: id-token: write` in the workflow.
- If the project doesn't exist on PyPI yet: https://pypi.org/manage/account/publishing/ → "Add a new pending publisher". The first successful publish then creates the project and converts this into a normal trusted publisher automatically.
- If it already exists: project page → Settings → Publishing → "Add a new publisher".
- Fill in exactly: **PyPI project name**, **Owner** (GitHub org/user), **Repository name**, **Workflow filename** (`deploy.yml`), **Environment name** (leave blank — this workflow doesn't declare a GitHub Environment).
- These fields are matched character-for-character against the workflow run's OIDC claims.

#### Cutting a release
1. Bump `version` in `pyproject.toml` and merge that change into the branch you release from (`main`) — the workflow builds whatever `pyproject.toml` says **on the tagged commit**, not on `dev`. Tagging before the merge silently rebuilds the previous version.
2. On the GitHub repo page: Releases → "Create a new release" → set the tag to match the version (e.g. `v0.1.2` for `0.1.2`) → publish.
3. PyPI versions are immutable: once a version is uploaded it can never be replaced, only [yanked](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/). Any fix, however small, needs a fresh version bump.
4. Verify: check the workflow run succeeded, then confirm the new version shows up at `https://pypi.org/project/<name>/`.

### (TODO) Documentation (`docs.yml`)
Docs build/publish belongs in its own workflow, separate from release:
- **Tooling**: [MkDocs](https://www.mkdocs.org/) (Markdown-based, simple) or [Sphinx](https://www.sphinx-doc.org/) (richer, common in scientific Python).
- **Hosting**: [Read the Docs](https://readthedocs.org/) auto-builds on push to `main` once you connect the repo — no workflow file needed beyond webhook setup. Alternative: build in Actions and deploy to GitHub Pages.
- **Triggers**: on push to `main` (publish) and on PRs (build-only, to catch broken docs before merge).
- Keep sources in `docs/`.

## 3. GitHub Apps:
- CodeRabbit or Copilot for automatic PR reviews (currently disabled)
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

# Contributing

Thanks for contributing to this sandbox! This project uses
[Pixi](https://pixi.sh) for reproducible environments.

## Local development

```bash
# Install the environment from pixi.lock (exact, reproducible)
pixi install

# Run the app
pixi run start

# Run tests with coverage
pixi run test

# Lint & format
pixi run ruff check .
pixi run ruff format .

# Run all pre-commit hooks on the whole tree
pixi run pre-commit run --all-files
```

Install the git pre-commit hooks once so they run automatically on staged files:

```bash
pixi run pre-commit install
```

## Branching model

```
feature/* → dev → main
```

- Branch off `dev` for new work (`feature/<short-name>`).
- Open PRs against **`dev`**, not `main`.
- `main` holds release-ready code; releases are published from GitHub Releases.

## Before opening a PR

- Tests pass (`pixi run test`)
- Lint & format clean
- Pre-commit hooks pass
- Never edit `pixi.lock` by hand — regenerate it with `pixi install`

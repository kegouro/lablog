# Release checklist

## Automated path

1. Merge to `main` with green CI.
2. Bump version in `pyproject.toml` + `CHANGELOG.md`.
3. Tag and push:
   ```bash
   git tag -a vX.Y.Z -m "lablog vX.Y.Z"
   git push origin vX.Y.Z
   ```
4. Workflow `.github/workflows/release.yml` builds UI + package, creates GitHub Release assets, and publishes to PyPI.

## PyPI publishing

Two options (first match wins in the workflow):

### A. API token (simplest)

1. Create a PyPI API token scoped to `jose-labarca-lablog`.
2. Add GitHub repo secret **`PYPI_API_TOKEN`**.
3. Re-run the Release workflow (tag push or `workflow_dispatch`).

### B. Trusted publishing (OIDC)

On PyPI → project **jose-labarca-lablog** → Publishing → Trusted publishers:

| Field | Value |
|---|---|
| Owner | `kegouro` |
| Repository | `lablog` |
| Workflow | `release.yml` |
| Environment | *(leave empty — workflow no longer scopes to env `pypi`)* |

If a previous publisher was registered with environment `pypi`, either update it to match or delete and recreate without environment.

## Re-publish after a failed PyPI job

GitHub Release may already exist; only PyPI needs retry:

```bash
gh workflow run release.yml -f tag=v0.2.0
```

(Requires `workflow_dispatch` on the default branch with this file merged.)

## Smoke after publish

```bash
pip install -U jose-labarca-lablog
lablog --help
python -c "import lablog; print(lablog.__version__ if hasattr(lablog,'__version__') else 'ok')"
```

Or from local wheel:

```bash
./scripts/smoke_install.sh
```

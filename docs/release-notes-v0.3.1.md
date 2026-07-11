# lablog v0.3.1

**Released:** 2026-07-11

## Highlights

Patch release that ships the production hardening and documentation that landed after v0.3.0.

### Hardening
- Atomic optimistic concurrency on document replace (`EventStore.append` + `expected_version`)
- Autosave serialization and 409 retry
- Lab mode flushes dirty cells on exit; cell insert/update/move return `version`
- `PageDetail` includes `project_id` / `updated_at`
- Snippet catalog fixes (`fit_line`, `simple_table`); title/project_id length bounds

### Documentation
- Expanded academic README (EN) + full Spanish twin `README.es.md`
- Real UI screenshots under `docs/assets/screenshots/`
- Keyboard shortcuts section; architecture mermaid diagrams

## Install

```bash
pip install -U "jose-labarca-lablog==0.3.1"
```

## Cite

See `CITATION.cff` (version 0.3.1). After Zenodo archives this tag, add the DOI to `CITATION.cff`.

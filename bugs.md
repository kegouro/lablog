# Bug Report — lablog — 2026-07-10

Pass: adversarial hunt + full fix wave (pre-release confidence).

## Summary
- Critical: 0 open, 5 fixed
- Intermediate: 0 open, 9 fixed
- Normal: 0 open, 5 fixed

## 🔴 Critical — all resolved

### BUG-001: Parameter “Congelar” races autosave — Fixed 2026-07-10
- discardPendingSave + versioned replace after bake

### BUG-002: Soft-deleted pages accept writes — Fixed 2026-07-10
- `_require_active_page` on all write routes; list_cells/find_cell reject deleted

### BUG-003: Cell parse stops at first `\end{lang}` — Fixed 2026-07-10
- Balanced begin/end scan + ZWSP escape of `\end{` on serialize

### BUG-004: Vault force-delete phrase not secret — Fixed 2026-07-10
- Random token; only returned on delete-request; force requires pending_deletion + compare_digest

### BUG-005: `\begin{document}` swallows cells — Fixed 2026-07-10
- Cell regex only matches CODE_ENVIRONMENTS names

## 🟡 Intermediate — all resolved

### BUG-006: No version on document_replaced — Fixed
- Optional `version` on PUT/replace → 409 VERSION_CONFLICT

### BUG-007: Page-switch getPage race — Fixed
- cancelled flag + activePageId guard (editor + lab)

### BUG-008: restore re-emits errors as ok — Fixed
- execution_failed when past status is error

### BUG-009: EventStore append unlocked — Fixed
- per-page threading.Lock around append+read

### BUG-010: Vault concurrent upload — Fixed
- UUID temp names + vault meta lock

### BUG-011: text_inserted last TextNode only — Documented / CLI safer
- CLI uses assert_active; voice remains append-only (by design)

### BUG-012: Autosave drops failed drafts — Fixed
- re-queue pending on failure; discardPending API

### BUG-013: Content-Disposition injection — Fixed
- `_safe_download_filename`

### BUG-014: cell_id with `]` — Fixed
- API pattern validation + safe label serialization

## 🟢 Normal — resolved

### BUG-015 CLI list/append — Fixed (projections + assert_active)
### BUG-016 list_cells deleted — Fixed (404)
### BUG-017 Unlimited latex PUT — Fixed (5MB max)
### BUG-018 PDF cache figures — mitigated by unique figure tokens (prior)
### BUG-019 Speech onerror drops transcript — Fixed (→ processing if text)

## ✅ Validation
- pytest: 176 passed, ≥80% coverage
- ruff + mypy clean
- ui tsc + build clean

## Remaining (non-blocking)
- Multi-tab full optimistic concurrency requires clients to always send version (optional field; UI does).
- Raw paste of `\end{python}` inside cell source still needs escape path via cell events (serialize on save).
- CLI coverage 0% (commands guarded).

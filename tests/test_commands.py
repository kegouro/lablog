from pathlib import Path

import pytest

from lablog.code_engine import EngineStartError
from lablog.commands import (
    CellNotFoundError,
    EngineExecutionError,
    PageDeletedError,
    UnsupportedLanguageError,
    create_page,
    delete_cell,
    delete_page,
    execute_cell,
    insert_cell,
    move_cell,
    replace_document,
    restore_version,
    update_cell,
)
from lablog.event_store import EventStore
from lablog.projections import find_cell, page_detail


def test_create_page_returns_page_id(tmp_path):
    store = EventStore(tmp_path)
    page_id = create_page(store, title="Test")
    assert isinstance(page_id, str)
    detail = page_detail(store, page_id)
    assert detail["title"] == "Test"


def test_replace_document_emits_event(tmp_path):
    store = EventStore(tmp_path)
    page_id = create_page(store, title="Test")
    replace_document(store, page_id, "hello world")
    events = store.get_events(page_id)
    assert events[-1].type == "document_replaced"


def _page_with_cell(store, source="1 + 1", language="python"):
    page_id = create_page(store, title="CellPage")
    insert_cell(store, page_id, cell_id="c1", language=language, source=source)
    return page_id


def test_insert_update_delete_move_cells(tmp_path):
    store = EventStore(tmp_path)
    page_id = _page_with_cell(store)

    update_cell(store, page_id, cell_id="c1", source="2 + 2")
    move_cell(store, page_id, cell_id="c1", new_index=0)
    delete_cell(store, page_id, cell_id="c1")

    events = store.get_events(page_id)
    assert [e.type for e in events[-3:]] == [
        "cell_updated",
        "cell_moved",
        "cell_deleted",
    ]


def test_execute_cell_not_found(tmp_path):
    store = EventStore(tmp_path)
    page_id = create_page(store, title="Empty")
    engine = object()  # no se llega a usar
    with pytest.raises(CellNotFoundError):
        execute_cell(store, page_id, "missing", engine=engine, figure_dir=Path("/tmp"))  # type: ignore[arg-type]


def test_execute_cell_unsupported_language(tmp_path):
    store = EventStore(tmp_path)
    page_id = _page_with_cell(store, language="markdown", source="# hi")
    engine = object()  # no se llega a usar
    with pytest.raises(UnsupportedLanguageError):
        execute_cell(store, page_id, "c1", engine=engine, figure_dir=Path("/tmp"))  # type: ignore[arg-type]


def test_execute_cell_emits_execution_failed_on_engine_start_error(tmp_path):
    store = EventStore(tmp_path)
    page_id = _page_with_cell(store)

    class BrokenEngine:
        def execute(self, *_args, **_kwargs):
            raise EngineStartError("kernel caído")

    with pytest.raises(EngineExecutionError):
        execute_cell(store, page_id, "c1", engine=BrokenEngine(), figure_dir=Path("/tmp"))

    events = store.get_events(page_id)
    failed = [e for e in events if e.type == "execution_failed"]
    assert len(failed) == 1
    assert failed[0].payload["ename"] == "EngineStartError"
    cell = find_cell(store, page_id, "c1")
    assert cell is not None
    assert cell.status == "error"
    assert "kernel caído" in (cell.output or "")


def test_execute_cell_emits_execution_failed_on_user_code_error(tmp_path):
    store = EventStore(tmp_path)
    page_id = _page_with_cell(store, source="1/0")

    class ErrorEngine:
        def execute(self, *_args, **_kwargs):
            from lablog.code_engine import ExecutionResult

            return ExecutionResult(status="error", text="ZeroDivisionError: division by zero")

    execute_cell(store, page_id, "c1", engine=ErrorEngine(), figure_dir=Path("/tmp"))

    updated = find_cell(store, page_id, "c1")
    assert updated is not None
    assert updated.status == "error"
    assert "ZeroDivisionError" in (updated.output or "")
    events = store.get_events(page_id)
    assert events[-1].type == "execution_failed"
    assert events[-1].payload["ename"] == "UserCodeError"


def test_execute_cell_emits_cell_executed_on_success(tmp_path):
    store = EventStore(tmp_path)
    page_id = _page_with_cell(store, source="2 + 2")

    class OkEngine:
        def execute(self, *_args, **_kwargs):
            from lablog.code_engine import ExecutionResult

            return ExecutionResult(status="ok", text="4")

    execute_cell(store, page_id, "c1", engine=OkEngine(), figure_dir=Path("/tmp"))

    updated = find_cell(store, page_id, "c1")
    assert updated is not None
    assert updated.status == "ok"
    assert updated.output == "4"
    events = store.get_events(page_id)
    assert events[-1].type == "cell_executed"
    assert events[-1].payload["output"] == "4"


def test_restore_version_replaces_document(tmp_path):
    store = EventStore(tmp_path)
    page_id = create_page(store, title="R")
    replace_document(store, page_id, "v1")
    replace_document(store, page_id, "v2")
    restore_version(store, page_id, event_index=1)
    detail = page_detail(store, page_id)
    assert "v1" in detail["raw"]


def test_restore_version_rejects_deleted_page(tmp_path):
    store = EventStore(tmp_path)
    page_id = create_page(store, title="Gone")
    delete_page(store, page_id)
    with pytest.raises(PageDeletedError):
        restore_version(store, page_id, event_index=0)

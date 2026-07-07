from lablog.commands import create_page, replace_document
from lablog.event_store import EventStore


def test_create_page_returns_summary(tmp_path):
    store = EventStore(tmp_path)
    summary = create_page(store, title="Test")
    assert summary["title"] == "Test"
    assert summary["page_id"]


def test_replace_document_returns_projection(tmp_path):
    store = EventStore(tmp_path)
    summary = create_page(store, title="Test")
    replace_document(store, summary["page_id"], "hello world")
    # La proyección se verifica a través del event store
    events = store.get_events(summary["page_id"])
    assert events[-1].type == "document_replaced"

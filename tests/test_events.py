from lablog.events import execution_failed


def test_execution_failed_event_has_traceback():
    event = execution_failed(
        page_id="p1",
        cell_id="c1",
        ename="ZeroDivisionError",
        evalue="division by zero",
        traceback=["Traceback (most recent call last):", "ZeroDivisionError: division by zero"],
    )
    assert event.type == "execution_failed"
    assert event.payload["cell_id"] == "c1"
    assert "traceback" in event.payload

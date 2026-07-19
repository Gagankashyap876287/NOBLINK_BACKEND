from datetime import datetime, timedelta

from app.core.constants import VISIT_INACTIVITY_MINUTES
from app.services.visit_service import VisitService


def test_single_ping_visit_duration_uses_entry_to_exit():

    service = VisitService.__new__(VisitService)
    entry = datetime(2026, 4, 19, 21, 25, 0)

    closed = service._close_visit(
        {
            "entryTime": entry,
            "lastPingTime": entry,
        }
    )

    assert closed["exitTime"] == entry + timedelta(minutes=VISIT_INACTIVITY_MINUTES)
    assert closed["durationMinutes"] == float(VISIT_INACTIVITY_MINUTES)
    assert closed["autoExited"] is True


def test_multi_ping_visit_duration_includes_inactivity_pad():
    service = VisitService.__new__(VisitService)
    entry = datetime(2026, 4, 19, 21, 25, 0)
    last_ping = entry + timedelta(minutes=15)

    closed = service._close_visit(
        {
            "entryTime": entry,
            "lastPingTime": last_ping,
        }
    )

    assert closed["exitTime"] == last_ping + timedelta(minutes=VISIT_INACTIVITY_MINUTES)
    assert closed["durationMinutes"] == 30.0

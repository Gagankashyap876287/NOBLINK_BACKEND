from datetime import datetime

import pytest

from app.services.alert_conditions.base import EvaluationContext
from app.services.alert_conditions.quiet_gap import QuietGapEvaluator


NMD_RULE = {
    "ruleId": "R2",
    "alertType": "NMD",
    "condition": "quiet_gap_minutes_gt",
    "threshold": "180",
    "appliesToZone": "any",
}


def _visit(**overrides):
    base = {
        "sensorId": "S1",
        "zone": "bathroom",
        "entryTime": datetime(2026, 4, 19, 8, 0),
        "lastPingTime": datetime(2026, 4, 19, 8, 10),
        "resident": "A",
        "room": "Bath",
        "facility": "F",
        "region": "R",
        "workflowName": "Standard Care",
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_nmd_does_not_fire_when_recent_motion_exists():
  
    context = EvaluationContext(
        visits=[_visit()],
        sensor_pings=[
            {
                "sensorId": "S1",
                "timestamp": datetime(2026, 4, 19, 10, 0),
                "eventType": "presence",
            },
            {
                "sensorId": "S1",
                "timestamp": datetime(2026, 4, 19, 11, 30),
                "eventType": "motion",
            },
        ],
        clock=datetime(2026, 4, 19, 12, 0),
    )

    matches = await QuietGapEvaluator().evaluate(NMD_RULE, context)
    assert matches == []


@pytest.mark.asyncio
async def test_nmd_fires_on_activity_ping_gap_over_threshold():
    
    context = EvaluationContext(
        visits=[_visit()],
        sensor_pings=[
            {
                "sensorId": "S1",
                "timestamp": datetime(2026, 4, 19, 6, 0),
                "eventType": "presence",
            },
            {
                "sensorId": "S1",
                "timestamp": datetime(2026, 4, 19, 10, 0),
                "eventType": "presence",
            },
        ],
        clock=datetime(2026, 4, 19, 10, 30),
    )

    matches = await QuietGapEvaluator().evaluate(NMD_RULE, context)
    assert len(matches) >= 1
    assert matches[0]["rule"]["ruleId"] == "R2"


@pytest.mark.asyncio
async def test_nmd_heartbeats_do_not_reset_silence():
    context = EvaluationContext(
        visits=[_visit()],
        sensor_pings=[
            {
                "sensorId": "S1",
                "timestamp": datetime(2026, 4, 19, 8, 0),
                "eventType": "presence",
            },
            {
                "sensorId": "S1",
                "timestamp": datetime(2026, 4, 19, 11, 0),
                "eventType": "heartbeat",
            },
        ],
        clock=datetime(2026, 4, 19, 12, 0),
    )

    matches = await QuietGapEvaluator().evaluate(NMD_RULE, context)
    assert len(matches) >= 1

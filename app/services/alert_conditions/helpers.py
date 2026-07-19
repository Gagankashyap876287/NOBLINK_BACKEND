from datetime import datetime, timedelta

from app.core.constants import NIGHT_END_HOUR, NIGHT_START_HOUR


def zone_applies(rule: dict, zone: str | None) -> bool:
    applies_to = (rule.get("appliesToZone") or "any").lower()

    if applies_to == "any":
        return True

    return (zone or "").lower() == applies_to


def threshold_number(rule: dict) -> float:
    return float(rule["threshold"])


def threshold_text(rule: dict) -> str:
    return str(rule["threshold"]).strip()


def is_night(moment: datetime) -> bool:
    hour = moment.hour
    return hour >= NIGHT_START_HOUR or hour < NIGHT_END_HOUR


def night_bucket(moment: datetime) -> str:
    if moment.hour < NIGHT_END_HOUR:
        return (moment - timedelta(days=1)).date().isoformat()

    return moment.date().isoformat()


def candidate(visit: dict, rule: dict) -> dict:
    return {"visit": visit, "rule": rule}

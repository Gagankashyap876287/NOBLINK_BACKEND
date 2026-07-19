from enum import Enum


class EventType(str, Enum):
    PRESENCE = "presence"
    MOTION = "motion"
    HEARTBEAT = "heartbeat"
    FALL_SUSPECTED = "fall_suspected"
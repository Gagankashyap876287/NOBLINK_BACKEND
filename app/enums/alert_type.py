from enum import Enum


class AlertType(str, Enum):
    PBO = "PBO"
    NMD = "NMD"
    FRQ = "FRQ"
    FALL = "FALL"
    OFFL = "OFFL"
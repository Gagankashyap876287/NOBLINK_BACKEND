from pydantic import BaseModel


class UploadResponse(BaseModel):
    success: bool
    message: str
    totalRecords: int
    insertedRecords: int


class SensorPingUploadResponse(BaseModel):
    success: bool
    message: str
    rawPingsInserted: int = 0
    visitsGenerated: int = 0
    alertsGenerated: int = 0
    alreadyStored: bool = False

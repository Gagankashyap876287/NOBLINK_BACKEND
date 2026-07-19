# Noblink Backend - API & assumptions

Base URL: `http://127.0.0.1:8000/api/v1`  
Interactive docs: http://127.0.0.1:8000/docs


## Note on "now" 

This dataset is not live. Whenever the system needs a current clock -
hours-open, offline detection, SLA breach, and related analytics -
we treat the latest `timestamp` present in `Sensor_Pings` / `sensor_pings`
as "now"


### Visit inactivity - 15 minutes (chosen)

We set `VISIT_INACTIVITY_MINUTES = 15`

What it does: When sessionizing visits, consecutive presence / motion /
fall_suspected pings on the same sensor that are <= 15 minutes apart belong to
the same visit. If the gap is longer than 15 minutes, the previous visit
is auto-exited and a new visit starts. Exit time is last activity ping; duration is entry -> exit. Heartbeats do not open or extend visits
(they only show the sensor is still online).

Why 15 minutes:

Prevents Fragmented Analytics: By using a 15-minute window, we group normal, intermittent movement into a single, meaningful visit record, preventing our reports from being flooded with hundreds of 'micro-visits'.

Ensures Reliable Alerting: It is short enough to accurately distinguish between separate room entries—ensuring that if a resident leaves and returns, it is treated as a new event—but long enough to maintain a continuous, 'live' record for as long as the resident is actively using the space.

Reduces Noise: This threshold filters out natural pauses in activity, ensuring that our SLA breach reports reflect genuine gaps in occupancy rather than the normal, minor fluctuations in resident behavior.


## Error shape

```json
{
  "success": false,
  "message": "human readable reason",
  "details": null
}
```

---

## API reference (routes + shapes)

Base path: `/api/v1`

Upload order to exercise the system: sensor-registry -> alert-rules ->
workflow-configs -> coordinators -> sensor-pings. 

### Route index

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health + DB + clock |
| GET | `/upload/config-status` | Config load status |
| GET | `/upload/export/{config_key}` | Export config CSV |
| POST | `/upload/sensor-registry` | Replace registry |
| POST | `/upload/alert-rules` | Replace alert rules |
| POST | `/upload/workflow-configs` | Replace workflows |
| POST | `/upload/coordinators` | Replace coordinators |
| POST | `/upload/sensor-pings` | Ingest pings -> visits -> alerts |
| GET | `/alerts` | List / filter alerts |
| GET | `/alerts/{alert_id}` | Alert detail + visit + events |
| GET | `/visits` | Visit history by sensor/resident |
| GET | `/workflows/{workflow_name}` | Workflow steps + SLA |
| GET | `/coordinators/{coordinator_id}` | Coordinator load |
| GET | `/analytics/fleet-summary` | Fleet KPIs |
| GET | `/analytics/breakdown` | Grouped risk/counts |
| GET | `/analytics/sla-breaches` | Past-SLA open alerts |
| GET | `/analytics/coordinators` | Coordinator performance |
| GET | `/analytics/activity` | Activity timeline |

### `GET /health`

```json
{
  "success": true,
  "status": "ok",
  "database": "up",
  "asOf": "2026-04-20T23:35:00"
}
```

### Upload

Bodies: `multipart/form-data`, field name `file` (CSV).  
Config POSTs replace the whole collection. Sensor pings max 5 MB.

#### `GET /upload/config-status`

```json
{
  "success": true,
  "configs": [
    {
      "key": "sensor-registry",
      "label": "sensor registry",
      "filename": "Sensor_Registry.csv",
      "recordCount": 10,
      "uploaded": true,
      "uploadedAt": "2026-07-19T07:34:22.351000"
    }
  ],
  "readyForPings": true
}
```

`key`: `sensor-registry` | `alert-rules` | `workflow-configs` | `coordinators`

#### `GET /upload/export/{config_key}`

Returns `csv` for a loaded config key, or 404 if empty.

#### `POST /upload/sensor-registry` | `alert-rules` | `workflow-configs` | `coordinators`

```json
{
  "success": true,
  "message": "sensor_registry uploaded successfully.",
  "totalRecords": 10,
  "insertedRecords": 10
}
```

#### `POST /upload/sensor-pings`

Requires all four configs. Builds visits + alerts unless pings already stored.

```json
{
  "success": true,
  "message": "Sensor pings processed successfully.",
  "rawPingsInserted": 300,
  "visitsGenerated": 136,
  "alertsGenerated": 35,
  "alreadyStored": false
}
```

Identical re-upload sets `alreadyStored: true` and does not rebuild.

### `GET /alerts`

Query (optional): `coordinatorId`, `status`, `region`, `resident`, `alertType`.

```json
{
  "success": true,
  "count": 56,
  "data": [
    {
      "_id": "6a5cc55ab02d628ebc849b64",
      "visitId": null,
      "sensorId": "SEN-BR-04",
      "resident": "A. Dlamini",
      "coordinatorId": "COORD-01",
      "ruleId": "R5",
      "alertType": "OFFL",
      "severity": 10,
      "riskScore": 10,
      "status": "OPEN",
      "workflow": {
        "workflowName": "Standard Care",
        "currentStep": 1,
        "currentStepName": "Initial Triage",
        "stepStartedAt": "2026-04-20T23:35:00"
      },
      "location": {
        "region": "Western Cape",
        "facility": "Oak Ridge",
        "room": "Bathroom 2",
        "zone": "bathroom"
      },
      "timing": {
        "createdAt": "2026-04-20T23:35:00",
        "updatedAt": "2026-04-20T23:35:00",
        "resolvedAt": null
      },
      "hoursOnCurrentStep": 0.0,
      "hoursOpen": 0.0,
      "asOf": "2026-04-20T23:35:00"
    }
  ]
}
```

`hoursOpen` / `hoursOnCurrentStep` use the platform clock (`asOf`).

### `GET /alerts/{alert_id}`

```json
{
  "success": true,
  "data": {
    "alert": { "...same shape as list item..." },
    "visit": {
      "_id": "...",
      "sensorId": "SEN-BR-01",
      "resident": "R. Naidoo",
      "room": "Bathroom 1",
      "zone": "bathroom",
      "facility": "Sunrise Manor",
      "region": "Western Cape",
      "workflowName": "Standard Care",
      "entryTime": "2026-04-19T08:00:00",
      "lastPingTime": "2026-04-19T08:22:00",
      "exitTime": "2026-04-19T08:37:00",
      "durationMinutes": 37.0,
      "pingCount": 3,
      "autoExited": true,
      "triggerEvents": ["presence", "motion"],
      "createdAt": "..."
    },
    "eventLog": [
      {
        "_id": "...",
        "alertId": "...",
        "eventType": "ALERT_CREATED",
        "timestamp": "2026-04-19T08:22:00",
        "note": null
      }
    ]
  }
}
```


### `GET /visits`

Requires `sensorId` and/or `resident`.

```json
{
  "success": true,
  "count": 12,
  "data": [
    {
      "_id": "...",
      "sensorId": "SEN-BR-01",
      "resident": "R. Naidoo",
      "room": "Bathroom 1",
      "zone": "bathroom",
      "facility": "Sunrise Manor",
      "region": "Western Cape",
      "workflowName": "Standard Care",
      "entryTime": "2026-04-19T08:00:00",
      "lastPingTime": "2026-04-19T08:22:00",
      "exitTime": "2026-04-19T08:37:00",
      "durationMinutes": 37.0,
      "pingCount": 3,
      "autoExited": true,
      "triggerEvents": ["presence"],
      "createdAt": "..."
    }
  ]
}
```

### `GET /workflows/{workflow_name}`


```json
{
  "success": true,
  "data": {
    "_id": "...",
    "workflowName": "Standard Care",
    "steps": [
      {
        "order": 1,
        "stepName": "Initial Triage",
        "maxResponseHours": 2,
        "requiresNote": false,
        "autoEscalate": true
      }
    ],
    "createdAt": "..."
  }
}
```

### `GET /coordinators/{coordinator_id}`

```json
{
  "success": true,
  "data": {
    "coordinator": {
      "_id": "...",
      "coordinatorId": "COORD-01",
      "name": "Thandi Nkosi",
      "role": "Senior Coordinator",
      "region": "Western Cape",
      "targetOpenCases": 8,
      "baselineResolutionHours": 4,
      "active": true,
      "createdAt": "..."
    },
    "load": {
      "openAlerts": 30,
      "targetOpenCases": 8,
      "pastSlaCount": 28,
      "openRisk": 1680,
      "asOf": "2026-04-20T23:35:00"
    }
  }
}
```

### Analytics

#### `GET /analytics/fleet-summary`

```json
{
  "success": true,
  "data": {
    "asOf": "2026-04-20T23:35:00",
    "totalAlerts": 56,
    "totalRiskExposure": 3150,
    "openRiskExposure": 3150,
    "slaBreachCount": 53,
    "byStatus": {
      "OPEN": { "count": 56, "totalRisk": 3150 },
      "RESOLVED": { "count": 0, "totalRisk": 0 },
      "DISMISSED": { "count": 0, "totalRisk": 0 }
    }
  }
}
```

#### `GET /analytics/breakdown?dimension=`

`dimension`: `region` | `alertType` | `resident` | `coordinator`

```json
{
  "success": true,
  "data": {
    "asOf": "2026-04-20T23:35:00",
    "dimension": "alertType",
    "groups": [
      { "key": "PBO", "count": 24, "totalRisk": 1920 },
      { "key": "NMD", "count": 16, "totalRisk": 720 }
    ]
  }
}
```

#### `GET /analytics/sla-breaches`

```json
{
  "success": true,
  "count": 53,
  "data": [
    {
      "_id": "...",
      "alertType": "PBO",
      "resident": "...",
      "coordinatorId": "COORD-01",
      "hoursOnCurrentStep": 12.5,
      "maxResponseHours": 2,
      "hoursOverSla": 10.5
    }
  ]
}
```

#### `GET /analytics/coordinators`

```json
{
  "success": true,
  "data": [
    {
      "coordinatorId": "COORD-01",
      "name": "Thandi Nkosi",
      "region": "Western Cape",
      "openAlertCount": 30,
      "targetOpenCases": 8,
      "openRisk": 1680,
      "breachCount": 28,
      "avgHoursOpen": 24.73,
      "baselineResolutionHours": 4,
      "avgVsBaselineDelta": 20.73
    }
  ]
}
```

#### `GET /analytics/activity?start=&end=`

ISO datetimes; `end` ≥ `start`.

```json
{
  "success": true,
  "data": {
    "start": "2026-04-19T00:00:00",
    "end": "2026-04-21T23:59:59",
    "series": [
      {
        "day": "2026-04-19",
        "total": 160,
        "byEventType": {
          "VISIT_OPENED": 69,
          "VISIT_CLOSED": 66,
          "ALERT_CREATED": 25
        }
      }
    ]
  }
}
```

---

## Setup

1. Run MongoDB and set `MONGO_URI` / `DB_NAME` in `.env`.
2. Create a virtualenv in `noblink-backend` and install `requirements.txt`.
3. Start the API with uvicorn on `app.main:app` (port 8000).
4. Optional: clear all collections with the `scripts.clear_db` module.
5. Upload sample CSVs from `sample_data/` in order: sensor-registry -> alert-rules ->
   workflow-configs -> coordinators -> sensor-pings (or use the Intake UI).

Interactive docs: http://127.0.0.1:8000/docs

---

## Architecture

```
CSV upload -> services -> repositories -> MongoDB
                ↓
         Pydantic models (validate shapes)

Ping path:  sensor_pings -> VisitService -> AlertService -> event logs
Read path:  query/analytics services -> aggregations / filters
```

## Tests

Install `requirements-dev.txt`, then run pytest against the `tests/` package.

Covers visit duration, NMD quiet-gap, CSV upload guards, config-before-pings,
and duplicate ping upload messaging.



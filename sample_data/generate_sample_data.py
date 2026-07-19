from datetime import datetime, timedelta
from pathlib import Path
import csv
import random

out = Path(__file__).resolve().parent
out.mkdir(exist_ok=True)

registry = [
    ["Sensor_ID", "Resident", "Room", "Zone", "Facility", "Region", "Workflow"],
    ["SEN-BR-01", "R. Naidoo", "Bathroom 1", "bathroom", "Sunrise Manor", "Western Cape", "Standard Care"],
    ["SEN-BR-02", "M. Okoye", "Ensuite", "bathroom", "Cedar Court", "Gauteng", "Standard Care"],
    ["SEN-RM-03", "J. Fourie", "Bedroom", "bedroom", "Sunrise Manor", "KwaZulu-Natal", "Critical Response"],
    ["SEN-BR-04", "A. Dlamini", "Bathroom 2", "bathroom", "Oak Ridge", "Western Cape", "Standard Care"],
    ["SEN-BR-05", "L. Petersen", "Bathroom 1", "bathroom", "Cedar Court", "Gauteng", "Standard Care"],
    ["SEN-RM-06", "S. Botha", "Bedroom", "bedroom", "Oak Ridge", "Western Cape", "Critical Response"],
    ["SEN-BR-07", "T. Mokoena", "Ensuite", "bathroom", "Sunrise Manor", "Western Cape", "Standard Care"],
    ["SEN-BR-08", "N. Abrahams", "Bathroom 3", "bathroom", "Cedar Court", "Gauteng", "Standard Care"],
    ["SEN-RM-09", "P. van Wyk", "Bedroom", "bedroom", "Sunrise Manor", "KwaZulu-Natal", "Critical Response"],
    ["SEN-BR-10", "K. Govender", "Bathroom 1", "bathroom", "Oak Ridge", "Western Cape", "Standard Care"],
]
with (out / "Sensor_Registry.csv").open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(registry)

rules = [
    ["Rule_ID", "Alert_Type", "Description", "Applies_To_Zone", "Condition", "Threshold", "Base_Severity"],
    ["R1", "PBO", "Prolonged Bathroom Occupancy", "bathroom", "visit_duration_minutes_gt", "20", "80"],
    ["R2", "NMD", "No Motion Detected", "any", "quiet_gap_minutes_gt", "180", "45"],
    ["R3", "FRQ", "Frequent Night Visits", "bathroom", "night_visits_count_gt", "3", "40"],
    ["R4", "FALL", "Suspected Fall", "any", "event_type_is", "fall_suspected", "95"],
    ["R5", "OFFL", "Sensor Offline", "any", "no_heartbeat_minutes_gt", "60", "10"],
]
with (out / "Alert_Rules.csv").open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rules)

workflows = [
    ["Workflow_Name", "Step_Name", "Step_Order", "Max_Response_Hours", "Requires_Note", "Auto_Escalate"],
    ["Standard Care", "Initial Triage", "1", "2", "No", "Yes"],
    ["Standard Care", "Caregiver Contact", "2", "4", "Yes", "Yes"],
    ["Standard Care", "Escalation Review", "3", "3", "Yes", "No"],
    ["Standard Care", "Welfare Check", "4", "6", "Yes", "Yes"],
    ["Standard Care", "Closed", "5", "0", "No", "No"],
    ["Critical Response", "Immediate Review", "1", "1", "No", "Yes"],
    ["Critical Response", "Dispatch", "2", "2", "Yes", "Yes"],
    ["Critical Response", "Closed", "3", "0", "No", "No"],
]
with (out / "Workflow_Configuration.csv").open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(workflows)

coordinators = [
    ["Coordinator_ID", "Name", "Role", "Region", "Target_Open_Cases", "Baseline_Resolution_Hours"],
    ["COORD-01", "Thandi Nkosi", "Senior Coordinator", "Western Cape", "8", "4"],
    ["COORD-02", "Johan Pretorius", "Coordinator", "Western Cape", "10", "5"],
    ["COORD-03", "Aisha Patel", "Coordinator", "Gauteng", "9", "4"],
    ["COORD-04", "Sipho Dube", "Junior Coordinator", "Gauteng", "6", "6"],
    ["COORD-05", "Nomsa Khumalo", "Team Lead", "KwaZulu-Natal", "12", "3"],
    ["COORD-06", "Erik van der Berg", "Coordinator", "KwaZulu-Natal", "8", "5"],
]
with (out / "Coordinator_Context.csv").open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(coordinators)

random.seed(42)
base = datetime(2026, 4, 19, 0, 0, 0)
pings = [["Sensor_ID", "Timestamp", "Event_Type", "Battery_Pct"]]


def add(sid, ts, et, bat):
    pings.append([sid, ts.strftime("%Y-%m-%dT%H:%M:%S"), et, bat])


# SEN-BR-01: long bathroom visit (~25 min) -> PBO
t = base + timedelta(hours=8)
add("SEN-BR-01", t, "presence", 88)
for m in [2, 5, 10, 14, 18, 22, 25]:
    add("SEN-BR-01", t + timedelta(minutes=m), "motion", 87)

# SEN-BR-02: night visits x5 -> FRQ
t = base + timedelta(hours=23)
for i in range(5):
    vt = t + timedelta(minutes=i * 40)
    add("SEN-BR-02", vt, "presence", 60)
    add("SEN-BR-02", vt + timedelta(minutes=3), "motion", 60)
    add("SEN-BR-02", vt + timedelta(minutes=6), "motion", 59)

# SEN-RM-03: fall
add("SEN-RM-03", base + timedelta(hours=9), "fall_suspected", 74)
add("SEN-RM-03", base + timedelta(hours=9, minutes=1), "motion", 74)

# SEN-BR-04: early heartbeat then silence -> OFFL
add("SEN-BR-04", base + timedelta(hours=7), "heartbeat", 12)

# SEN-BR-05: normal short visits + heartbeats
for day in range(2):
    for h in [7, 12, 18]:
        t = base + timedelta(days=day, hours=h)
        add("SEN-BR-05", t, "presence", 70)
        add("SEN-BR-05", t + timedelta(minutes=4), "motion", 70)
        add("SEN-BR-05", t + timedelta(hours=2), "heartbeat", 69)

# SEN-RM-06: quiet gap > 180 min -> NMD
add("SEN-RM-06", base + timedelta(hours=6), "presence", 80)
add("SEN-RM-06", base + timedelta(hours=6, minutes=5), "motion", 80)
add("SEN-RM-06", base + timedelta(hours=20), "presence", 79)
add("SEN-RM-06", base + timedelta(hours=20, minutes=3), "motion", 79)

# SEN-BR-07: mix across 2 days
for day in range(2):
    for h in [8, 15, 21]:
        t = base + timedelta(days=day, hours=h, minutes=random.randint(0, 20))
        add("SEN-BR-07", t, "presence", 85 - day)
        add("SEN-BR-07", t + timedelta(minutes=random.randint(2, 8)), "motion", 85 - day)
        if random.random() > 0.5:
            add("SEN-BR-07", t + timedelta(minutes=12), "motion", 84 - day)

# SEN-BR-08: another long visit -> PBO
t = base + timedelta(days=1, hours=10)
add("SEN-BR-08", t, "presence", 55)
for m in [3, 8, 12, 16, 21, 24]:
    add("SEN-BR-08", t + timedelta(minutes=m), "motion", 55)

# SEN-RM-09: heartbeats + fall
for h in range(0, 24, 4):
    add("SEN-RM-09", base + timedelta(hours=h), "heartbeat", 90)
add("SEN-RM-09", base + timedelta(days=1, hours=14), "fall_suspected", 88)

# SEN-BR-10: steady activity
for day in range(2):
    for h in range(0, 24, 3):
        t = base + timedelta(days=day, hours=h)
        add("SEN-BR-10", t, "heartbeat", 77)
        if h in (8, 13, 19):
            add("SEN-BR-10", t + timedelta(minutes=10), "presence", 77)
            add("SEN-BR-10", t + timedelta(minutes=15), "motion", 76)

extra_sensors = ["SEN-BR-01", "SEN-BR-05", "SEN-BR-07", "SEN-BR-10"]
while len(pings) < 302:
    sid = random.choice(extra_sensors)
    day = random.randint(0, 1)
    h = random.randint(0, 23)
    m = random.randint(0, 59)
    t = base + timedelta(days=day, hours=h, minutes=m)
    et = random.choice(["heartbeat", "motion", "presence"])
    add(sid, t, et, random.randint(40, 95))

body = sorted(pings[1:], key=lambda row: row[1])
pings = [pings[0]] + body

with (out / "Sensor_Pings.csv").open("w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(pings)

print(f"Wrote {len(pings) - 1} pings to {out}")

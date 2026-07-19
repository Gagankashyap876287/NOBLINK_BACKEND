from enum import Enum


class CoordinatorRole(str, Enum):
    JUNIOR_COORDINATOR = "Junior Coordinator"
    COORDINATOR = "Coordinator"
    SENIOR_COORDINATOR = "Senior Coordinator"
    TEAM_LEAD = "Team Lead"
    MANAGER = "Manager"
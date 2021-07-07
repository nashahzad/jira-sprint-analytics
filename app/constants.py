from enum import Enum


class SprintStates(Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    FUTURE = "FUTURE"


class IssueTypeEnum(Enum):
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"


REPORT_COLUMNS = [
    "Sprint",
    "Commitment",
    "Completed",
    "4-Sprint Average",
    "Scope Change",
    "Planned Capacity",
    "Capacity Achieved",
    "4-Sprint Capacity Achieved",
    "4-Sprint Smoothed Average",
    "Unpointed Issues",
    "Unpointed Stories",
    "Unpointed Tasks",
    "Bug Tickets",
    "Priority Points",
    "Non-Priority Points",
]

DEFAULT_STORY_POINTS_FIELD_NAME = "customfield_10591"

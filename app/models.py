from datetime import datetime
from typing import List, Optional

from jira import Issue
from pydantic import BaseModel, validator

from app.constants import DEFAULT_STORY_POINTS_FIELD_NAME


class EnvConfig(BaseModel):
    jira_token: str
    email: str
    server_url: str


class ReportCommandLineArgs(BaseModel):
    planned_capacities: List[float]
    board_id: int
    project_name: str
    story_points_field: str = DEFAULT_STORY_POINTS_FIELD_NAME
    complete_status: str
    priority_epics: Optional[List[str]] = []
    past_n_sprints: Optional[int]

    @validator("priority_epics")
    def set_priority_epics(cls, priority_epics):
        if priority_epics is None:
            return []
        return priority_epics


class VisualizationCommandLineArgs(BaseModel):
    project_name: str


class ManagerConfig(BaseModel):
    jira_token: str
    email: str
    server_url: str

    planned_capacities: List[float]
    board_id: int
    project_name: str
    story_points_field: str
    complete_status: str
    priority_epics: List[str]
    past_n_sprints: Optional[int]


class SprintIssues(BaseModel):
    sprint_id: str
    issues: List[Issue]

    class Config:
        arbitrary_types_allowed = True


class JiraTicket(BaseModel):
    issue_type: str
    story_points: Optional[int]
    epic_key: Optional[str]
    status: str
    date_added: datetime


class UnpointedBreakdown(BaseModel):
    unpointed_stories: int
    unpointed_tasks: int
    unpointed_bugs: int

    @property
    def unpointed_sum(self) -> int:
        return self.unpointed_stories + self.unpointed_tasks + self.unpointed_bugs


class PriorityPointsBreakdown(BaseModel):
    priority_points: int
    non_priority_points: int


class SprintMetrics(BaseModel):
    planned_capacity: float
    commitment: int
    completed: int
    scope_change: int

    start_date: datetime
    end_date: datetime

    unpointed_breakdown: UnpointedBreakdown
    priority_breakdown: PriorityPointsBreakdown

    @property
    def sprint_name(self) -> str:
        sprint_name = (
            f"{self.start_date.month}/{self.start_date.day} - "
            f"{self.end_date.month}/{self.end_date.day}"
        )
        return sprint_name

    @property
    def capacity_achieved(self) -> float:
        return self.completed / self.planned_capacity

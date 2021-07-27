from __future__ import absolute_import

from datetime import datetime
from typing import List, Optional, Dict

import pytz
from jira import JIRA, Issue

from app.constants import IssueTypeEnum, SprintStates
from app.models import (
    ManagerConfig,
    SprintMetrics,
    UnpointedBreakdown,
    PriorityPointsBreakdown,
    JiraTicket,
    SprintIssues,
)
from app.utils import get_manager_config


class JIRAManager:
    @classmethod
    def build(cls):
        config = get_manager_config()
        jira = JIRA(
            server=config.server_url,
            basic_auth=(config.email, config.jira_token),
        )
        return cls(jira, config)

    def __init__(self, jira: JIRA, config: ManagerConfig):
        self.jira = jira
        self.config = config

    def get_sprint_metrics(self) -> List[SprintMetrics]:
        sprints = self._get_sprint_issues()
        metrics = []
        for index, sprint_issues in enumerate(sprints):
            tickets = self._parse_issues(sprint_issues.issues)
            sprint_info = self._get_sprint_info(sprint_issues.sprint_id)
            start_date = self._get_sprint_start_date(sprint_info)
            end_date = self._get_sprint_end_date(sprint_info)

            commitment = self._get_initial_sprint_commitment(tickets, start_date)
            completed = self._get_completed_story_points(tickets)
            scope_change = self._get_scope_change(tickets, start_date)
            unpointed_breakdown = self._get_unpointed_breakdown(tickets)
            priority_breakdown = self._priority_points_breakdown(tickets)

            planned_capacity = (
                self.config.planned_capacities[index]
                if index < len(self.config.planned_capacities)
                else 0
            )

            sprint_metrics = SprintMetrics(
                planned_capacity=planned_capacity,
                commitment=commitment,
                completed=completed,
                scope_change=scope_change,
                start_date=start_date,
                end_date=end_date,
                unpointed_breakdown=unpointed_breakdown,
                priority_breakdown=priority_breakdown,
            )
            metrics.append(sprint_metrics)
        return metrics

    def _parse_issues(self, issues: List[Issue]) -> List[JiraTicket]:
        tickets: List[JiraTicket] = []
        for issue in issues:
            issue_type = issue.fields.issuetype.name
            story_points = self._get_issue_story_points(issue)
            epic_key = self._get_epic_key(issue)
            status = issue.fields.status.name
            date_added = self._get_date_issue_added_to_sprint(issue)
            ticket = JiraTicket(
                issue_type=issue_type,
                story_points=story_points,
                epic_key=epic_key,
                status=status,
                date_added=date_added,
            )
            tickets.append(ticket)
        return tickets

    def _priority_points_breakdown(
        self, tickets: List[JiraTicket]
    ) -> PriorityPointsBreakdown:
        priority_points = 0
        non_priority_points = 0

        for ticket in tickets:
            if ticket.story_points is None:
                continue

            if (
                ticket.epic_key is not None
                and ticket.epic_key in self.config.priority_epics
            ):
                priority_points += ticket.story_points
            else:
                non_priority_points += ticket.story_points

        priority_points_breakdown = PriorityPointsBreakdown(
            priority_points=priority_points,
            non_priority_points=non_priority_points,
        )
        return priority_points_breakdown

    def _get_completed_story_points(self, tickets: List[JiraTicket]) -> int:
        completed_story_points = 0
        for ticket in tickets:
            if ticket.status == self.config.complete_status:
                completed_story_points += (
                    ticket.story_points if ticket.story_points is not None else 0
                )

        return completed_story_points

    def _get_unpointed_breakdown(self, tickets: List[JiraTicket]) -> UnpointedBreakdown:
        breakdown = {}

        for ticket in tickets:
            if ticket.story_points is None:
                issue_type = ticket.issue_type
                breakdown[issue_type] = breakdown.get(issue_type, 0) + 1

        unpointed_breakdown = UnpointedBreakdown(
            unpointed_stories=breakdown.get(IssueTypeEnum.STORY.value, 0),
            unpointed_tasks=breakdown.get(IssueTypeEnum.TASK.value, 0),
            unpointed_bugs=breakdown.get(IssueTypeEnum.BUG.value, 0),
        )
        return unpointed_breakdown

    def _get_initial_sprint_commitment(
        self, tickets: List[JiraTicket], start_date: datetime
    ) -> int:
        commitment = 0

        for ticket in tickets:
            if ticket.date_added < start_date:
                issue_points = ticket.story_points
                commitment += issue_points if issue_points is not None else 0
        return commitment

    def _get_scope_change(self, tickets: List[JiraTicket], start_date: datetime) -> int:
        scope_change = 0

        for ticket in tickets:
            if ticket.date_added > start_date:
                issue_points = ticket.story_points
                scope_change += issue_points if issue_points is not None else 0

        return scope_change

    def _get_sprint_issues(self) -> List[SprintIssues]:
        sprints = self.jira.sprints(board_id=self.config.board_id)
        sprints = reversed(sprints)

        if self.config.past_n_sprints is not None:
            states = [SprintStates.CLOSED.value, SprintStates.ACTIVE.value]
            limit = self.config.past_n_sprints + 1
        else:
            states = [SprintStates.ACTIVE.value]
            limit = 1

        filtered_sprints = list(filter(lambda sprint: sprint.state in states, sprints))
        filtered_sprints = filtered_sprints[:limit]

        sprint_issues = []
        for sprint in filtered_sprints:
            jql = f"project = {self.config.project_name} AND sprint = {sprint.id}"
            issues = self.jira.search_issues(
                jql_str=jql,
                fields=f"{self.config.story_points_field},status,issuetype,parent",
                expand="changelog",
            )
            sprint_issue = SprintIssues(sprint_id=sprint.id, issues=issues)
            sprint_issues.append(sprint_issue)
        return sprint_issues

    def _get_issue_story_points(self, issue: Issue) -> Optional[int]:
        issue_points = issue.raw["fields"][self.config.story_points_field]
        return issue_points

    def _get_epic_key(self, issue: Issue) -> Optional[str]:
        if hasattr(issue.fields, "parent"):
            return issue.fields.parent.key
        else:
            return None

    def _get_date_issue_added_to_sprint(self, issue: Issue) -> datetime:
        added_dt = None
        for history in issue.changelog.histories:
            if history.items[0].field == "Sprint":
                added_dt = history.created
        added_datetime = self._convert_created_history_timestamp(added_dt)
        return added_datetime

    def _convert_created_history_timestamp(self, dt: str) -> datetime:
        date = datetime.strptime(dt, "%Y-%m-%dT%X.%f%z")
        utc_datetime = date.replace(tzinfo=pytz.UTC)
        return utc_datetime

    def _get_sprint_info(self, sprint_id: str) -> Dict:
        sprint_info = self.jira.sprint_info(
            board_id=self.config.board_id, sprint_id=sprint_id
        )
        return sprint_info

    def _get_sprint_start_date(self, sprint_info: Dict) -> datetime:
        start_date = datetime.strptime(sprint_info["startDate"], "%d/%b/%y %I:%M %p")
        utc_start_date = pytz.UTC.localize(start_date)
        return utc_start_date

    def _get_sprint_end_date(self, sprint_info: Dict) -> datetime:
        end_date = datetime.strptime(sprint_info["endDate"], "%d/%b/%y %I:%M %p")
        utc_start_date = pytz.UTC.localize(end_date)
        return utc_start_date

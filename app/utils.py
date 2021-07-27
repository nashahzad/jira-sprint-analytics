import os
import argparse

from yaml import safe_load

from app.constants import DEFAULT_STORY_POINTS_FIELD_NAME
from app.models import (
    EnvConfig,
    ManagerConfig,
    ReportCommandLineArgs,
    VisualizationCommandLineArgs,
)


def _get_config_file_configs(config_filename: str) -> ReportCommandLineArgs:
    with open(config_filename) as f:
        config = safe_load(f)

    args = ReportCommandLineArgs(**config)
    return args


def _get_config_file_visualization_configs(
    config_filename: str,
) -> VisualizationCommandLineArgs:
    with open(config_filename) as f:
        config = safe_load(f)

    args = VisualizationCommandLineArgs(**config)
    return args


def _get_report_command_line_args() -> ReportCommandLineArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-file",
        dest="config_filename",
        type=str,
        help="Optional config file containing the configuration by which to "
        "generate a report with, if provided then "
        "the other args not required.",
        required=False,
    )
    parser.add_argument(
        "--planned-capacities",
        dest="planned_capacities",
        type=float,
        nargs="*",
        help="The team's planned capacities for previous sprints. "
        "In order of most current to the oldest sprint's planned capacities.",
        required=False,
        default=[],
    )
    parser.add_argument(
        "--board-id", dest="board_id", type=int, help="JIRA Board ID", required=False
    )
    parser.add_argument(
        "--project-name",
        dest="project_name",
        type=str,
        help="JIRA Project Name",
        required=False,
    )
    parser.add_argument(
        "--story-points-field",
        dest="story_points_field",
        type=str,
        help="JIRA Story Points API field name",
        required=False,
        default=DEFAULT_STORY_POINTS_FIELD_NAME,
    )
    parser.add_argument(
        "--complete-status",
        dest="complete_status",
        type=str,
        help="JIRA Issue status to indicate an Issue is done",
        required=False,
    )
    parser.add_argument(
        "--priority-epics",
        dest="priority_epics",
        type=str,
        nargs="*",
        help="Optional list of keys of the priority epics",
        required=False,
        default=[],
    )
    parser.add_argument(
        "--past-n-sprints",
        dest="past_n_sprints",
        type=int,
        nargs="*",
        help="Optionally grab metrics for the past N sprints, "
        "if left out then only the currently active sprint's metrics "
        "will be fetched",
        required=False,
        default=None,
    )
    namespace = parser.parse_args()
    if namespace.config_filename is not None:
        args = _get_config_file_configs(namespace.config_filename)
        return args

    args = ReportCommandLineArgs(
        planned_capacity=namespace.planned_capacity,
        board_id=namespace.board_id,
        project_name=namespace.project_name,
        story_points_field=namespace.story_points_field,
        complete_status=namespace.complete_status,
        priority_epics=namespace.priority_epics,
    )
    return args


def get_visualization_command_line_args() -> VisualizationCommandLineArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-file",
        dest="config_filename",
        help="Optional config file that can be supplied and then the other"
        "args are not required",
        type=str,
        required=False,
    )
    parser.add_argument(
        "--project-name",
        dest="project_name",
        help="JIRA Project Name",
        type=str,
        required=False,
    )
    namespace = parser.parse_args()
    if namespace.config_filename is not None:
        args = _get_config_file_visualization_configs(namespace.config_filename)
        return args

    args = VisualizationCommandLineArgs(project_name=namespace.project_name)
    return args


def _get_env_config() -> EnvConfig:
    config = EnvConfig(
        jira_token=os.environ["JIRA_TOKEN"],
        email=os.environ["JIRA_EMAIL"],
        server_url=os.environ["JIRA_SERVER"],
    )
    return config


def get_manager_config() -> ManagerConfig:
    env_config = _get_env_config()
    command_line_args = _get_report_command_line_args()

    config = ManagerConfig(**env_config.dict(), **command_line_args.dict())
    return config

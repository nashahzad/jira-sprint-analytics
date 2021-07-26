from typing import Optional, List

from app.constants import REPORT_COLUMNS
from app.models import SprintMetrics
import pandas as pd
import plotly.express as ex


class ReportManager:
    @classmethod
    def build(cls, project_name: str):
        try:
            df = pd.read_csv(f"reports/{project_name}_sprint_metrics.csv")
        except FileNotFoundError:
            df = pd.DataFrame(columns=REPORT_COLUMNS)
        return cls(df, project_name)

    def __init__(self, df: pd.DataFrame, project_name: str):
        self.df = df
        self.project_name = project_name

    def visualize_report(self) -> None:
        df = pd.melt(
            self.df,
            id_vars=self.df.columns[0],
            value_vars=self.df.columns[1:],
        )
        figure = ex.line(
            df, x="Sprint", y="value", color="variable", template="plotly_dark"
        )
        figure.show()

    def create_or_update_report(self, sprint_metrics: List[SprintMetrics]) -> None:
        sprint_names = [metrics.sprint_name for metrics in sprint_metrics]
        for sprint_name in sprint_names:
            self._remove_existing_current_sprint_entry(sprint_name)

        for sprint_metric in sprint_metrics:
            four_sprint_average = self._get_four_sprint_completed_average(
                sprint_metric.completed
            )
            four_sprint_capacity_achieved_avg = (
                self._get_four_sprint_capacity_achieved_average(
                    sprint_metric.capacity_achieved
                )
            )
            four_sprint_smoothed_capacity_avg = (
                self._get_four_sprint_smoothed_capacity_achieved_average(
                    sprint_metric.completed, sprint_metric.planned_capacity
                )
            )
            row = {
                "Sprint": sprint_metric.sprint_name,
                "Commitment": sprint_metric.commitment,
                "Completed": sprint_metric.completed,
                "4-Sprint Average": four_sprint_average,
                "Scope Change": sprint_metric.scope_change,
                "Planned Capacity": sprint_metric.planned_capacity,
                "Capacity Achieved": self._format_float_as_percent(
                    sprint_metric.capacity_achieved
                ),
                "4-Sprint Capacity Achieved": four_sprint_capacity_achieved_avg,
                "4-Sprint Smoothed Average": four_sprint_smoothed_capacity_avg,
                "Unpointed Issues": sprint_metric.unpointed_breakdown.unpointed_sum,
                "Unpointed Stories": sprint_metric.unpointed_breakdown.unpointed_stories,
                "Unpointed Tasks": sprint_metric.unpointed_breakdown.unpointed_tasks,
                "Bug Tickets": sprint_metric.unpointed_breakdown.unpointed_bugs,
                "Priority Points": sprint_metric.priority_breakdown.priority_points,
                "Non-Priority Points": sprint_metric.priority_breakdown.non_priority_points,
            }

            self.df = self.df.append(row, ignore_index=True)
        self.df.to_csv(
            f"reports/{self.project_name}_sprint_metrics.csv",
            index=False,
            mode="w+",
        )

    def _remove_existing_current_sprint_entry(self, sprint_name: str) -> None:
        if len(self.df) == 0:
            return None
        self.df = self.df[self.df.Sprint != sprint_name]

    def _format_float_as_percent(self, value: float) -> str:
        formatted_float = "{0:.2%}".format(value)
        return formatted_float

    def _get_four_sprint_smoothed_capacity_achieved_average(
        self, completed: int, planned_capacity: float
    ) -> Optional[str]:
        if len(self.df) < 4:
            return None

        completed_sum = self.df.Completed.iloc[-3:].sum() + completed
        planned_capacity_sum = (
            self.df["Planned Capacity"].iloc[-3:].sum() + planned_capacity
        )
        average = completed_sum / planned_capacity_sum
        formatted_average = self._format_float_as_percent(average)
        return formatted_average

    def _get_four_sprint_capacity_achieved_average(
        self, capacity_achieved: float
    ) -> Optional[str]:
        if len(self.df) < 4:
            return None

        values = [float(ca[:-1]) for ca in self.df["Capacity Achieved"].iloc[-3:]]
        average = (sum(values) + capacity_achieved * 100) / 4 / 100
        formatted_average = self._format_float_as_percent(average)
        return formatted_average

    def _get_four_sprint_completed_average(self, completed: int) -> Optional[str]:
        if len(self.df) < 4:
            return None

        average = (self.df.Completed.iloc[-3:].sum() + completed) / 4
        return average

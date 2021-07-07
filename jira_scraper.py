from dotenv import load_dotenv

from app.managers.jira_managers import JIRAManager
from app.managers.report_managers import ReportManager

load_dotenv()


if __name__ == "__main__":
    manager = JIRAManager.build()
    sprint_metrics = manager.get_sprint_metrics()
    report_manager = ReportManager.build(manager.config.project_name)
    report_manager.create_or_update_report(sprint_metrics)

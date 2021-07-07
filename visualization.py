from app.managers.report_managers import ReportManager
from app.utils import get_visualization_command_line_args

if __name__ == "__main__":
    args = get_visualization_command_line_args()
    report_manager = ReportManager.build(args.project_name)
    report_manager.visualize_report()

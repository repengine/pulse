import argparse
from simulation_engine.forecasting.forecast_log_viewer import load_and_display_forecasts
from simulation_engine.forecasting.forecast_exporter import export_forecast_csv, export_forecast_markdown

def main():
    parser = argparse.ArgumentParser(description="Pulse Forecast Tools CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    view_parser = subparsers.add_parser("view", help="View top forecasts")
    view_parser.add_argument("--top", type=int, default=5, help="Number of forecasts to show")
    view_parser.add_argument("--sort_by", type=str, default="confidence", help="Sort forecasts by this field")
    view_parser.add_argument("--log_dir", type=str, default="forecast_output", help="Directory of forecast logs")
    view_parser.add_argument("--domain", type=str, help="Filter forecasts by domain")

    export_parser = subparsers.add_parser("export", help="Export forecasts to CSV/Markdown")
    export_parser.add_argument("--log_dir", type=str, default="forecast_output", help="Directory of forecast logs")
    export_parser.add_argument("--csv_out", type=str, default="forecast_summary.csv", help="CSV output file")
    export_parser.add_argument("--md_out", type=str, default="forecast_summary.md", help="Markdown output file")
    export_parser.add_argument("--domain", type=str, help="Filter forecasts by domain")

    args = parser.parse_args()

    if args.command == "view":
        load_and_display_forecasts(
            log_dir=args.log_dir,
            top_n=args.top,
            sort_by=args.sort_by,
            domain_filter=args.domain
        )

    elif args.command == "export":
        export_forecast_csv(
            output_file=args.csv_out,
            log_dir=args.log_dir,
            domain_filter=args.domain
        )
        export_forecast_markdown(
            output_file=args.md_out,
            log_dir=args.log_dir,
            domain_filter=args.domain
        )
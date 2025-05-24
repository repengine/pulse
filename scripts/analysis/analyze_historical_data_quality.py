"""
Analyze the quality of historical timeline data for retrodiction training:
1. Evaluate data completeness across priority variables
2. Verify historical depth (at least 3-5 years)
3. Check for missing values and imputation effectiveness
4. Analyze temporal alignment across variables
5. Generate summary report with visualizations
"""

import os
import json
import pandas as pd
import logging
import datetime as dt
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("historical_data_analysis.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Constants
HISTORICAL_TIMELINE_DIR = "data/historical_timeline"
VARIABLE_CATALOG_PATH = f"{HISTORICAL_TIMELINE_DIR}/variable_catalog.json"
VERIFICATION_REPORT_PATH = f"{HISTORICAL_TIMELINE_DIR}/verification_report.json"
OUTPUT_DIR = f"{HISTORICAL_TIMELINE_DIR}/reports"
MIN_YEARS = 3
TARGET_YEARS = 5

# Priority financial and economic indicators (same as in improve_historical_data.py)
PRIORITY_VARIABLES = [
    # Market indices
    "spx_close",  # S&P 500
    "vix_close",  # VIX volatility index
    "us_10y_yield",  # US 10-year Treasury yield
    # Economic indicators
    "gdp_growth_annual",  # GDP growth
    "real_gdp",  # Real GDP
    "cpi_yoy",  # CPI year-over-year
    "inflation",  # Inflation
    "unemployment_rate_fred",  # Unemployment rate
    # Commodities
    "gold_futures",  # Gold
    "crude_oil_futures_wti",  # Oil
    "wti_crude_oil_price",  # WTI Oil price
    "brent_crude_oil_price",  # Brent Oil price
    # Additional financial indicators
    "crypto_bitcoin_usd",  # Bitcoin price
    "vanguard_total_stock_market_etf",
    "personal_consumption_expenditures",
    "nonfarm_payroll",
    "total_nonfarm_payroll",
    "federal_debt_total",
]


def load_variable_catalog() -> dict:
    """Load the variable catalog."""
    with open(VARIABLE_CATALOG_PATH, "r") as f:
        return json.load(f)


def load_verification_report() -> dict:
    """Load the current verification report."""
    with open(VERIFICATION_REPORT_PATH, "r") as f:
        return json.load(f)


def get_latest_transformation(variable_name: str) -> Optional[str]:
    """Get the path to the latest transformation result for a variable."""
    transform_dir = f"{HISTORICAL_TIMELINE_DIR}/{variable_name}/transformations"

    if not os.path.exists(transform_dir):
        logger.warning(f"No transformations directory found for {variable_name}")
        return None

    try:
        # Get the most recent transformation file
        files = list(Path(transform_dir).glob("*_transform_result.json"))
        if not files:
            logger.warning(f"No transformation results found for {variable_name}")
            return None

        # Sort by modification time, most recent first
        latest_file = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
        return str(latest_file)
    except Exception as e:
        logger.error(f"Error getting latest transformation for {variable_name}: {e}")
        return None


def load_transformation_data(filepath: str) -> Optional[dict]:
    """Load the transformation data from a file."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading transformation data from {filepath}: {e}")
        return None


def analyze_variable_data(variable_name: str) -> Dict[str, Any]:
    """Analyze the data for a single variable."""
    results = {
        "variable_name": variable_name,
        "has_data": False,
        "historical_years": 0,
        "data_points": 0,
        "completeness_pct": 0,
        "has_missing_values": False,
        "missing_value_count": 0,
        "date_range": None,
        "min_value": None,
        "max_value": None,
        "mean_value": None,
    }

    # Get the latest transformation
    transform_path = get_latest_transformation(variable_name)

    if not transform_path:
        logger.warning(f"No transformation found for {variable_name}")
        return results

    # Load the transformation data
    data = load_transformation_data(transform_path)

    if not data or "values" not in data:
        logger.warning(f"Invalid transformation data for {variable_name}")
        return results

    try:
        # Convert to pandas DataFrame
        df = pd.DataFrame(data["values"])
        df["date"] = pd.to_datetime(df["date"])

        # Calculate date range
        min_date = df["date"].min()
        max_date = df["date"].max()
        date_range = (max_date - min_date).days / 365.25  # Approximate years

        # Check for missing values
        missing_count = df["value"].isna().sum()

        # Update results
        results.update(
            {
                "has_data": True,
                "historical_years": round(date_range, 2),
                "data_points": len(df),
                "completeness_pct": 100.0 * (len(df) - missing_count) / len(df)
                if len(df) > 0
                else 0,
                "has_missing_values": missing_count > 0,
                "missing_value_count": missing_count,
                "date_range": f"{min_date.date()} to {max_date.date()}",
                "min_value": None
                if df["value"].isna().all()
                else float(df["value"].min()),
                "max_value": None
                if df["value"].isna().all()
                else float(df["value"].max()),
                "mean_value": None
                if df["value"].isna().all()
                else float(df["value"].mean()),
            }
        )

        return results
    except Exception as e:
        logger.error(f"Error analyzing data for {variable_name}: {e}")
        return results


def analyze_temporal_alignment(
    variable_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Analyze temporal alignment across variables."""
    results = {
        "variables_analyzed": len(variable_results),
        "variables_with_data": sum(
            1 for v in variable_results.values() if v["has_data"]
        ),
        "min_years": min(
            [v["historical_years"] for v in variable_results.values() if v["has_data"]]
            or [0]
        ),
        "max_years": max(
            [v["historical_years"] for v in variable_results.values() if v["has_data"]]
            or [0]
        ),
        "avg_years": sum(
            [v["historical_years"] for v in variable_results.values() if v["has_data"]]
        )
        / sum(1 for v in variable_results.values() if v["has_data"])
        if sum(1 for v in variable_results.values() if v["has_data"]) > 0
        else 0,
        "variables_meeting_min_years": sum(
            1 for v in variable_results.values() if v["historical_years"] >= MIN_YEARS
        ),
        "percent_meeting_min_years": 100.0
        * sum(
            1 for v in variable_results.values() if v["historical_years"] >= MIN_YEARS
        )
        / sum(1 for v in variable_results.values() if v["has_data"])
        if sum(1 for v in variable_results.values() if v["has_data"]) > 0
        else 0,
        "variables_meeting_target_years": sum(
            1
            for v in variable_results.values()
            if v["historical_years"] >= TARGET_YEARS
        ),
        "percent_meeting_target_years": 100.0
        * sum(
            1
            for v in variable_results.values()
            if v["historical_years"] >= TARGET_YEARS
        )
        / sum(1 for v in variable_results.values() if v["has_data"])
        if sum(1 for v in variable_results.values() if v["has_data"]) > 0
        else 0,
    }

    return results


def generate_visualizations(
    variable_results: Dict[str, Dict[str, Any]], alignment_results: Dict[str, Any]
) -> Dict[str, str]:
    """Generate visualizations for the analysis."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    visualization_paths = {}

    try:
        # 1. Historical depth by variable
        plt.figure(figsize=(14, 8))

        # Filter out variables without data
        data_vars = {k: v for k, v in variable_results.items() if v["has_data"]}

        # Sort by historical years
        sorted_vars = sorted(
            data_vars.items(), key=lambda x: x[1]["historical_years"], reverse=True
        )
        var_names = [x[0] for x in sorted_vars]
        years = [x[1]["historical_years"] for x in sorted_vars]

        plt.barh(var_names, years)

        # Add a line for MIN_YEARS
        plt.axvline(
            x=MIN_YEARS,
            color="r",
            linestyle="--",
            label=f"Minimum Target ({MIN_YEARS} years)",
        )

        # Add a line for TARGET_YEARS
        plt.axvline(
            x=TARGET_YEARS,
            color="g",
            linestyle="--",
            label=f"Ideal Target ({TARGET_YEARS} years)",
        )

        plt.xlabel("Historical Data (Years)")
        plt.ylabel("Variable")
        plt.title("Historical Depth by Variable")
        plt.legend()
        plt.tight_layout()

        # Save the figure
        historical_depth_path = f"{OUTPUT_DIR}/historical_depth.png"
        plt.savefig(historical_depth_path)
        plt.close()

        visualization_paths["historical_depth"] = historical_depth_path

        # 2. Data completeness by variable
        plt.figure(figsize=(14, 8))

        # Sort by completeness percentage
        sorted_vars = sorted(
            data_vars.items(), key=lambda x: x[1]["completeness_pct"], reverse=True
        )
        var_names = [x[0] for x in sorted_vars]
        completeness = [x[1]["completeness_pct"] for x in sorted_vars]

        _bars = plt.barh(var_names, completeness)

        # Add a line for 95% completeness
        plt.axvline(x=95, color="r", linestyle="--", label="95% Completeness")

        # Add a line for 99% completeness
        plt.axvline(x=99, color="g", linestyle="--", label="99% Completeness")

        plt.xlabel("Data Completeness (%)")
        plt.ylabel("Variable")
        plt.title("Data Completeness by Variable")
        plt.legend()
        plt.tight_layout()

        # Save the figure
        completeness_path = f"{OUTPUT_DIR}/data_completeness.png"
        plt.savefig(completeness_path)
        plt.close()

        visualization_paths["data_completeness"] = completeness_path

        # 3. Summary metrics
        plt.figure(figsize=(10, 6))

        metrics = [
            f"Variables with data: {alignment_results['variables_with_data']}/{alignment_results['variables_analyzed']}",
            f"Min years: {alignment_results['min_years']:.2f}",
            f"Max years: {alignment_results['max_years']:.2f}",
            f"Avg years: {alignment_results['avg_years']:.2f}",
            f"Meeting min ({MIN_YEARS} years): {alignment_results['variables_meeting_min_years']}/{alignment_results['variables_with_data']} ({alignment_results['percent_meeting_min_years']:.1f}%)",
            f"Meeting target ({TARGET_YEARS} years): {alignment_results['variables_meeting_target_years']}/{alignment_results['variables_with_data']} ({alignment_results['percent_meeting_target_years']:.1f}%)",
        ]

        # Create a table
        plt.axis("off")
        plt.title("Summary Metrics", fontsize=16)

        table = plt.table(
            cellText=[[m] for m in metrics],
            loc="center",
            cellLoc="left",
            colWidths=[0.8],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1, 2)

        # Save the figure
        summary_path = f"{OUTPUT_DIR}/summary_metrics.png"
        plt.savefig(summary_path, bbox_inches="tight")
        plt.close()

        visualization_paths["summary_metrics"] = summary_path

        return visualization_paths
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        return visualization_paths


def generate_report(
    variable_results: Dict[str, Dict[str, Any]],
    alignment_results: Dict[str, Any],
    visualization_paths: Dict[str, str],
) -> str:
    """Generate a comprehensive report of the analysis."""
    try:
        # Create report directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Generate timestamp
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"{OUTPUT_DIR}/historical_data_quality_report_{timestamp}.html"

        # Create HTML report
        with open(report_path, "w") as f:
            f.write(f"""
            <html>
            <head>
                <title>Historical Data Quality Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 1200px; margin: 0 auto; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .good {{ color: green; }}
                    .warning {{ color: orange; }}
                    .bad {{ color: red; }}
                    .summary {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    img {{ max-width: 100%; height: auto; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1>Historical Data Quality Report</h1>
                <p>Generated on: {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <p>Variables analyzed: <strong>{alignment_results["variables_analyzed"]}</strong></p>
                    <p>Variables with data: <strong>{alignment_results["variables_with_data"]}</strong></p>
                    <p>Historical depth: <strong>{alignment_results["min_years"]:.2f} to {alignment_results["max_years"]:.2f} years</strong> (average: {alignment_results["avg_years"]:.2f} years)</p>
                    <p>Variables meeting minimum target ({MIN_YEARS} years): <strong class="{("good" if alignment_results["percent_meeting_min_years"] >= 80 else "warning" if alignment_results["percent_meeting_min_years"] >= 50 else "bad")}">{alignment_results["variables_meeting_min_years"]}/{alignment_results["variables_with_data"]} ({alignment_results["percent_meeting_min_years"]:.1f}%)</strong></p>
                    <p>Variables meeting ideal target ({TARGET_YEARS} years): <strong class="{("good" if alignment_results["percent_meeting_target_years"] >= 80 else "warning" if alignment_results["percent_meeting_target_years"] >= 50 else "bad")}">{alignment_results["variables_meeting_target_years"]}/{alignment_results["variables_with_data"]} ({alignment_results["percent_meeting_target_years"]:.1f}%)</strong></p>
                </div>
                
                <h2>Visualizations</h2>
            """)

            # Add visualizations
            for name, path in visualization_paths.items():
                if os.path.exists(path):
                    rel_path = os.path.relpath(path, HISTORICAL_TIMELINE_DIR)
                    f.write(f"<h3>{name.replace('_', ' ').title()}</h3>\n")
                    f.write(f'<img src="../{rel_path}" alt="{name}" />\n')

            # Variable details table
            f.write("""
                <h2>Variable Details</h2>
                <table>
                    <tr>
                        <th>Variable</th>
                        <th>Has Data</th>
                        <th>Historical Years</th>
                        <th>Data Points</th>
                        <th>Completeness</th>
                        <th>Missing Values</th>
                        <th>Date Range</th>
                        <th>Min Value</th>
                        <th>Max Value</th>
                        <th>Mean Value</th>
                    </tr>
            """)

            # Sort variables by historical years (descending)
            sorted_vars = sorted(
                variable_results.items(),
                key=lambda x: x[1]["historical_years"] if x[1]["has_data"] else 0,
                reverse=True,
            )

            for var_name, var_results in sorted_vars:
                completeness_class = (
                    "good"
                    if var_results["completeness_pct"] >= 95
                    else "warning"
                    if var_results["completeness_pct"] >= 80
                    else "bad"
                )
                years_class = (
                    "good"
                    if var_results["historical_years"] >= TARGET_YEARS
                    else "warning"
                    if var_results["historical_years"] >= MIN_YEARS
                    else "bad"
                )

                f.write(f"""
                    <tr>
                        <td>{var_name}</td>
                        <td>{"Yes" if var_results["has_data"] else "No"}</td>
                        <td class="{years_class if var_results["has_data"] else ""}">{var_results["historical_years"]:.2f}</td>
                        <td>{var_results["data_points"]}</td>
                        <td class="{completeness_class if var_results["has_data"] else ""}">{var_results["completeness_pct"]:.2f}%</td>
                        <td>{"Yes" if var_results["has_missing_values"] else "No"} ({var_results["missing_value_count"]})</td>
                        <td>{var_results["date_range"] if var_results["has_data"] else "N/A"}</td>
                        <td>{var_results["min_value"] if var_results["min_value"] is not None else "N/A"}</td>
                        <td>{var_results["max_value"] if var_results["max_value"] is not None else "N/A"}</td>
                        <td>{f"{var_results['mean_value']:.4f}" if var_results["mean_value"] is not None else "N/A"}</td>
                    </tr>
                """)

            f.write("""
                </table>
                
                <h2>Recommendations</h2>
                <ul>
            """)

            # Generate recommendations
            if alignment_results["percent_meeting_min_years"] < 80:
                f.write(
                    f"<li>Increase historical depth for variables below the {MIN_YEARS}-year minimum threshold.</li>"
                )

            incomplete_vars = [
                v
                for v in variable_results.values()
                if v["has_data"] and v["completeness_pct"] < 95
            ]
            if incomplete_vars:
                f.write(
                    "<li>Improve data completeness for the following variables:</li>"
                )
                f.write("<ul>")
                for v in sorted(incomplete_vars, key=lambda x: x["completeness_pct"]):
                    f.write(
                        f"<li>{v['variable_name']} ({v['completeness_pct']:.2f}% complete)</li>"
                    )
                f.write("</ul>")

            missing_vars = [
                v["variable_name"]
                for v in variable_results.values()
                if not v["has_data"]
            ]
            if missing_vars:
                f.write("<li>Implement data ingestion for missing variables:</li>")
                f.write("<ul>")
                for var in missing_vars:
                    f.write(f"<li>{var}</li>")
                f.write("</ul>")

            f.write("""
                </ul>
                
                <h2>Conclusion</h2>
                <p>This report provides an overview of the historical timeline data quality for retrodiction training. Based on the analysis, further improvements may be needed to ensure sufficient historical depth and data completeness across all priority variables.</p>
            </body>
            </html>
            """)

        logger.info(f"Generated report at {report_path}")
        return report_path
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return ""


def main():
    """Main function to analyze historical data quality."""
    logger.info("Starting historical data quality analysis")

    try:
        # Analyze each priority variable
        variable_results = {}

        for variable_name in PRIORITY_VARIABLES:
            logger.info(f"Analyzing {variable_name}...")
            variable_results[variable_name] = analyze_variable_data(variable_name)

        # Analyze temporal alignment
        alignment_results = analyze_temporal_alignment(variable_results)

        # Generate visualizations
        visualization_paths = generate_visualizations(
            variable_results, alignment_results
        )

        # Generate report
        report_path = generate_report(
            variable_results, alignment_results, visualization_paths
        )

        if report_path:
            logger.info(f"Analysis complete. Report available at: {report_path}")
            print(f"Analysis complete. Report available at: {report_path}")
        else:
            logger.error("Failed to generate report")
            print("Failed to generate report")

    except Exception as e:
        logger.error(f"Error in main process: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()

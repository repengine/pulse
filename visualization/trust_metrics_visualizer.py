"""
trust_metrics_visualizer.py

Visualizes trust metrics and Bayesian statistics for rules and variables.

Author: Pulse v0.32
"""

import matplotlib.pyplot as plt
from typing import Dict, Any, Optional
import os
from core.bayesian_trust_tracker import bayesian_trust_tracker
from core.pulse_learning_log import generate_trust_report


def plot_trust_evolution(
    key: str, kind: str = "variable", save_path: Optional[str] = None
):
    """
    Plot the evolution of trust metrics over time.

    Args:
        key: Variable or rule key
        kind: 'variable' or 'rule'
        save_path: Optional path to save the figure
    """
    timestamps = bayesian_trust_tracker.timestamps.get(key, [])
    if not timestamps:
        print(f"No timestamp data available for {kind} {key}")
        return

    times, values = zip(*timestamps)

    # Convert to relative times in hours
    start_time = min(times)
    rel_times = [(t - start_time) / 3600 for t in times]

    plt.figure(figsize=(10, 6))
    plt.plot(rel_times, values, "b-", linewidth=2)

    # Add confidence intervals if we have at least 5 data points
    if len(times) >= 5:
        ci_low, ci_high = bayesian_trust_tracker.get_confidence_interval(key)
        plt.axhline(y=ci_low, color="r", linestyle="--", alpha=0.5)
        plt.axhline(y=ci_high, color="r", linestyle="--", alpha=0.5)
        plt.axhline(
            y=bayesian_trust_tracker.get_trust(key), color="g", linestyle="-", alpha=0.5
        )

    plt.title(f"Trust Evolution for {kind.capitalize()} {key}")
    plt.xlabel("Time (hours)")
    plt.ylabel("Trust Score")
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

    plt.close()


def plot_trust_histogram(
    kind: str = "all", min_samples: int = 5, save_path: Optional[str] = None
):
    """
    Plot histogram of trust scores.

    Args:
        kind: 'variable', 'rule', or 'all'
        min_samples: Minimum samples to include
        save_path: Optional path to save the figure
    """
    trust_scores = []
    labels = []

    report = generate_trust_report(min_samples)

    # Combine high and low trust items for comprehensive view
    all_items = (
        report["high_trust"]
        + report["low_trust"]
        + report["high_confidence"]
        + report["low_confidence"]
    )

    # Deduplicate by key
    seen_keys = set()
    unique_items = []
    for item in all_items:
        if item["key"] not in seen_keys:
            seen_keys.add(item["key"])
            unique_items.append(item)

    # Filter by kind if specified
    filtered_items = unique_items
    if kind != "all":
        filtered_items = [item for item in unique_items if item["key"].startswith(kind)]

    if not filtered_items:
        print(f"No {kind} data with minimum {min_samples} samples available")
        return

    for item in filtered_items:
        trust_scores.append(item["trust"])
        labels.append(item["key"])

    plt.figure(figsize=(12, 6))

    # Plot histogram
    plt.hist(trust_scores, bins=10, alpha=0.7, color="blue", edgecolor="black")

    plt.title(f"Trust Score Distribution ({kind})")
    plt.xlabel("Trust Score")
    plt.ylabel("Frequency")
    plt.grid(True, alpha=0.3)

    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

    plt.close()


def plot_confidence_vs_trust(
    kind: str = "all", min_samples: int = 5, save_path: Optional[str] = None
):
    """
    Scatter plot of confidence vs trust scores.

    Args:
        kind: 'variable', 'rule', or 'all'
        min_samples: Minimum samples to include
        save_path: Optional path to save the figure
    """
    trust_scores = []
    confidence_scores = []
    sample_sizes = []
    labels = []

    report = generate_trust_report(min_samples)
    all_items = (
        report["high_trust"]
        + report["low_trust"]
        + report["high_confidence"]
        + report["low_confidence"]
    )

    # Deduplicate by key
    seen_keys = set()
    unique_items = []
    for item in all_items:
        if item["key"] not in seen_keys:
            seen_keys.add(item["key"])
            unique_items.append(item)

    # Filter by kind if specified
    filtered_items = unique_items
    if kind != "all":
        filtered_items = [item for item in unique_items if item["key"].startswith(kind)]

    if not filtered_items:
        print(f"No {kind} data with minimum {min_samples} samples available")
        return

    for item in filtered_items:
        trust_scores.append(item["trust"])
        confidence_scores.append(item["confidence"])
        sample_sizes.append(item["sample_size"])
        labels.append(item["key"])

    plt.figure(figsize=(12, 8))

    # Calculate marker sizes based on sample size (scaled for visibility)
    marker_sizes = [20 + 5 * min(20, s) for s in sample_sizes]

    # Create scatter plot
    scatter = plt.scatter(
        trust_scores,
        confidence_scores,
        s=marker_sizes,
        c=trust_scores,
        cmap="viridis",
        alpha=0.7,
        edgecolors="black",
        linewidths=1,
    )

    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label("Trust Score")

    # Add annotations for top N points
    top_n = min(10, len(labels))
    sorted_indices = sorted(
        range(len(sample_sizes)), key=lambda i: sample_sizes[i], reverse=True
    )

    for i in sorted_indices[:top_n]:
        plt.annotate(
            labels[i],
            (trust_scores[i], confidence_scores[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    plt.title(f"Confidence vs Trust ({kind})")
    plt.xlabel("Trust Score")
    plt.ylabel("Confidence Score")
    plt.grid(True, alpha=0.3)

    # Add reference lines
    plt.axhline(y=0.5, color="gray", linestyle="--", alpha=0.5)
    plt.axvline(x=0.5, color="gray", linestyle="--", alpha=0.5)

    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()

    plt.close()


def generate_trust_dashboard(output_dir: str = "trust_dashboard"):
    """
    Generate a complete trust metrics dashboard.

    Args:
        output_dir: Directory to save dashboard files
    """
    os.makedirs(output_dir, exist_ok=True)

    # Generate summary report
    report = generate_trust_report(min_samples=5)

    # Plot trust histogram for all, variables, and rules
    plot_trust_histogram(
        "all", save_path=os.path.join(output_dir, "trust_histogram_all.png")
    )
    plot_trust_histogram(
        "R", save_path=os.path.join(output_dir, "trust_histogram_rules.png")
    )
    plot_trust_histogram(
        "V", save_path=os.path.join(output_dir, "trust_histogram_variables.png")
    )

    # Plot confidence vs trust
    plot_confidence_vs_trust(
        "all", save_path=os.path.join(output_dir, "confidence_vs_trust_all.png")
    )
    plot_confidence_vs_trust(
        "R", save_path=os.path.join(output_dir, "confidence_vs_trust_rules.png")
    )
    plot_confidence_vs_trust(
        "V", save_path=os.path.join(output_dir, "confidence_vs_trust_variables.png")
    )

    # Plot top 5 and bottom 5 trust evolutions
    top_rules = sorted(report["high_trust"], key=lambda x: x["trust"], reverse=True)[:5]
    bottom_rules = sorted(report["low_trust"], key=lambda x: x["trust"])[:5]

    for item in top_rules:
        plot_trust_evolution(
            item["key"],
            "rule" if item["key"].startswith("R") else "variable",
            save_path=os.path.join(output_dir, f"trust_evolution_{item['key']}.png"),
        )

    for item in bottom_rules:
        plot_trust_evolution(
            item["key"],
            "rule" if item["key"].startswith("R") else "variable",
            save_path=os.path.join(output_dir, f"trust_evolution_{item['key']}.png"),
        )

    # Generate HTML dashboard
    generate_html_dashboard(output_dir, report)

    print(f"Trust dashboard generated in {output_dir}")


def generate_html_dashboard(output_dir: str, report: Dict[str, Any]):
    """
    Generate an HTML dashboard from the trust report and visualizations.

    Args:
        output_dir: Directory with visualization files
        report: Trust report dictionary
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pulse Trust Metrics Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .row { display: flex; flex-wrap: wrap; margin: 10px -10px; }
            .col { padding: 10px; box-sizing: border-box; }
            .col-6 { width: 50%; }
            .col-12 { width: 100%; }
            .card { border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 20px; }
            .card-header { background-color: #f8f9fa; margin: -15px -15px 15px; padding: 10px 15px; border-bottom: 1px solid #ddd; }
            .metric { text-align: center; padding: 10px; }
            .metric-value { font-size: 24px; font-weight: bold; }
            .metric-label { font-size: 14px; color: #666; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f8f9fa; }
            tr:hover { background-color: #f5f5f5; }
            .visualizations img { max-width: 100%; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Pulse Trust Metrics Dashboard</h1>
            <p>Generated at: TIMESTAMP</p>
            
            <div class="row">
                <div class="col col-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Trust Summary</h2>
                        </div>
                        <div class="row">
                            <div class="col col-6">
                                <div class="metric">
                                    <div class="metric-value">TOTAL_ENTITIES</div>
                                    <div class="metric-label">Total Tracked Entities</div>
                                </div>
                            </div>
                            <div class="col col-6">
                                <div class="metric">
                                    <div class="metric-value">ACTIVE_ENTITIES</div>
                                    <div class="metric-label">Active Entities</div>
                                </div>
                            </div>
                            <div class="col col-6">
                                <div class="metric">
                                    <div class="metric-value">AVG_TRUST</div>
                                    <div class="metric-label">Average Trust Score</div>
                                </div>
                            </div>
                            <div class="col col-6">
                                <div class="metric">
                                    <div class="metric-value">AVG_CONFIDENCE</div>
                                    <div class="metric-label">Average Confidence</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col col-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>High Trust Entities</h2>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Key</th>
                                    <th>Trust</th>
                                    <th>Confidence</th>
                                    <th>Sample Size</th>
                                </tr>
                            </thead>
                            <tbody>
                                HIGH_TRUST_TABLE
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col col-12">
                    <div class="card">
                        <div class="card-header">
                            <h2>Low Trust Entities</h2>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Key</th>
                                    <th>Trust</th>
                                    <th>Confidence</th>
                                    <th>Sample Size</th>
                                </tr>
                            </thead>
                            <tbody>
                                LOW_TRUST_TABLE
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="card visualizations">
                <div class="card-header">
                    <h2>Trust Visualizations</h2>
                </div>
                <div class="row">
                    <div class="col col-6">
                        <h3>Trust Distribution (All)</h3>
                        <img src="trust_histogram_all.png" alt="Trust Histogram">
                    </div>
                    <div class="col col-6">
                        <h3>Confidence vs Trust (All)</h3>
                        <img src="confidence_vs_trust_all.png" alt="Confidence vs Trust">
                    </div>
                </div>
                <div class="row">
                    <div class="col col-6">
                        <h3>Trust Distribution (Rules)</h3>
                        <img src="trust_histogram_rules.png" alt="Rule Trust Histogram">
                    </div>
                    <div class="col col-6">
                        <h3>Confidence vs Trust (Rules)</h3>
                        <img src="confidence_vs_trust_rules.png" alt="Rule Confidence vs Trust">
                    </div>
                </div>
                <div class="row">
                    <div class="col col-6">
                        <h3>Trust Distribution (Variables)</h3>
                        <img src="trust_histogram_variables.png" alt="Variable Trust Histogram">
                    </div>
                    <div class="col col-6">
                        <h3>Confidence vs Trust (Variables)</h3>
                        <img src="confidence_vs_trust_variables.png" alt="Variable Confidence vs Trust">
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    # Replace placeholders
    import datetime

    html = html.replace(
        "TIMESTAMP", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    html = html.replace("TOTAL_ENTITIES", str(report["summary"]["total_entities"]))
    html = html.replace("ACTIVE_ENTITIES", str(report["summary"]["active_entities"]))
    html = html.replace("AVG_TRUST", f"{report['summary']['avg_trust']:.3f}")
    html = html.replace("AVG_CONFIDENCE", f"{report['summary']['avg_confidence']:.3f}")

    # Generate high trust table rows
    high_trust_rows = ""
    for item in sorted(report["high_trust"], key=lambda x: x["trust"], reverse=True):
        high_trust_rows += f"""
        <tr>
            <td>{item["key"]}</td>
            <td>{item["trust"]:.3f}</td>
            <td>{item["confidence"]:.3f}</td>
            <td>{item["sample_size"]}</td>
        </tr>
        """
    html = html.replace("HIGH_TRUST_TABLE", high_trust_rows)

    # Generate low trust table rows
    low_trust_rows = ""
    for item in sorted(report["low_trust"], key=lambda x: x["trust"]):
        low_trust_rows += f"""
        <tr>
            <td>{item["key"]}</td>
            <td>{item["trust"]:.3f}</td>
            <td>{item["confidence"]:.3f}</td>
            <td>{item["sample_size"]}</td>
        </tr>
        """
    html = html.replace("LOW_TRUST_TABLE", low_trust_rows)

    # Write HTML file
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    # Example usage
    import random

    # Simulate some data for testing
    for i in range(20):
        rule_id = f"R{i + 1:03d}"
        for j in range(random.randint(5, 20)):
            success = random.random() > 0.3
            bayesian_trust_tracker.update(rule_id, success)

    # Generate dashboard
    generate_trust_dashboard()

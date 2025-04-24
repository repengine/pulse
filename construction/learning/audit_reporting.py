"""
audit_reporting.py

AuditReportingEngine: Auto-generates reports and visualizations of learning engine changes, rule/variable updates, anomalies, and remediation actions. Summarizes and visualizes learning log events. CLI for generating and exporting audit reports.
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

class AuditReportingEngine:
    def __init__(self, log_path="logs/learning_log.jsonl"):
        self.log_path = log_path
        self.df = None
        if os.path.exists(log_path):
            self.df = pd.read_json(log_path, lines=True)
        else:
            self.df = pd.DataFrame()

    def summarize_events(self):
        if self.df.empty:
            print("No events to summarize.")
            return {}
        summary = self.df['event'].value_counts().to_dict() if 'event' in self.df else {}
        print("Event summary:", summary)
        return summary

    def plot_event_timeline(self, output_path=None):
        if self.df.empty or 'timestamp' not in self.df:
            print("No events or timestamps to plot.")
            return
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        event_counts = self.df.groupby([pd.Grouper(key='timestamp', freq='D'), 'event']).size().unstack(fill_value=0)
        event_counts.plot(figsize=(10, 6))
        plt.title('Learning Events Over Time')
        plt.xlabel('Date')
        plt.ylabel('Event Count')
        plt.tight_layout()
        if output_path:
            plt.savefig(output_path)
            print(f"Timeline plot saved to {output_path}")
        else:
            plt.show()

    def export_report(self, path="learning_audit_report.md"):
        summary = self.summarize_events()
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Learning Audit Report\n\nGenerated: {datetime.utcnow().isoformat()}\n\n")
            f.write("## Event Summary\n\n")
            for event, count in summary.items():
                f.write(f"- {event}: {count}\n")
            f.write("\n## Sample Events\n\n")
            if not self.df.empty:
                sample = self.df.head(10)
                f.write(sample.to_markdown(index=False))
        print(f"Audit report exported to {path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Learning Audit Reporting CLI")
    parser.add_argument("--summary", action="store_true", help="Print event summary")
    parser.add_argument("--timeline", type=str, help="Plot event timeline and save to file")
    parser.add_argument("--export", type=str, help="Export audit report to markdown file")
    args = parser.parse_args()
    engine = AuditReportingEngine()
    if args.summary:
        engine.summarize_events()
    if args.timeline:
        engine.plot_event_timeline(output_path=args.timeline)
    if args.export:
        engine.export_report(path=args.export)

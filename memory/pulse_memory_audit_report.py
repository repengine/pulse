"""
pulse_memory_audit_report.py

Reports on forecast memory usage and retention effectiveness.

Usage:
    audit_memory(memory)
"""

from typing import Optional
from memory.forecast_memory import ForecastMemory


def audit_memory(memory: ForecastMemory, csv_path: Optional[str] = None):
    """
    Prints and optionally exports memory audit report.
    """
    try:
        print(f"Total forecasts stored: {len(memory._memory)}")
        domains = set(f.get("domain", "unspecified") for f in memory._memory)
        print(f"Domains: {domains}")
        if csv_path:
            import csv

            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["forecast_id", "domain", "confidence"])
                for entry in memory._memory:
                    writer.writerow(
                        [
                            entry.get("forecast_id"),
                            entry.get("domain", "unspecified"),
                            entry.get("confidence", ""),
                        ]
                    )
            print(f"Audit exported to {csv_path}")
    except Exception as e:
        print(f"[MemoryAudit] Error: {e}")

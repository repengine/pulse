"""
Prometheus metrics utility for Pulse
"""

from prometheus_client import Counter, Histogram, start_http_server
import os

signal_ingest_counter = Counter(
    "pulse_signal_ingest_total", "Total number of ingested signals", ["source"]
)
signal_score_histogram = Histogram(
    "pulse_signal_trust_score", "Distribution of trust scores for ingested signals"
)

# Optionally, start a Prometheus HTTP server in worker
PROMETHEUS_PORT = int(os.getenv("PULSE_PROMETHEUS_PORT", "9100"))


def start_metrics_server():
    start_http_server(PROMETHEUS_PORT)

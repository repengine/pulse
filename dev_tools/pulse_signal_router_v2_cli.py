"""
pulse_signal_router_cli.py

CLI Runner for Pulse Signal Router v2 (Corrected for IRIS Core)

Allows manual injection of signals for testing the Pulse signal ingestion and routing system.

Author: Pulse-IRIS Development Team
Version: 0.427A (Corrected)
"""

import argparse
from datetime import datetime, timezone

# Corrected imports
try:
    from ingestion.pulse_signal_router_v2 import PulseSignalRouter
    from ingestion.iris_symbolism import IrisSymbolismTagger
    from ingestion.iris_trust import IrisTrustScorer
    from ingestion.iris_archive import IrisArchive
except ImportError:
    from ingestion.pulse_signal_router_v2 import PulseSignalRouter
    from ingestion.iris_symbolism import IrisSymbolismTagger
    from ingestion.iris_trust import IrisTrustScorer
    from ingestion.iris_archive import IrisArchive


def main():
    parser = argparse.ArgumentParser(description="Pulse Signal Router CLI")
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        help="Type of the signal (symbolic, trust, etc.)",
    )
    parser.add_argument(
        "--source", type=str, required=True, help="Source identifier for the signal"
    )
    parser.add_argument(
        "--payload",
        type=str,
        required=True,
        help="Payload content (format: key1=value1,key2=value2)",
    )
    args = parser.parse_args()

    # Initialize IRIS Core modules
    symbolism = IrisSymbolismTagger()
    trust = IrisTrustScorer()
    archive = IrisArchive()

    router = PulseSignalRouter(symbolism, trust, archive)

    # Parse payload into dict
    payload_dict = {}
    try:
        pairs = args.payload.split(",")
        for pair in pairs:
            key, value = pair.split("=")
            payload_dict[key.strip()] = float(value.strip())  # Assume numeric payloads
    except Exception as e:
        print(
            f"[CLI Error] Failed to parse payload. Expected format key1=value1,key2=value2. Error: {e}"
        )
        return

    # Build signal
    signal = {
        "type": args.type,
        "source": args.source,
        "payload": payload_dict,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Route the signal
    try:
        router.route_signal(signal)
        print(f"[PulseSignalRouter CLI] Signal routed successfully: {signal}")
    except Exception as e:
        print(f"[CLI Error] Failed to route signal. Error: {e}")


if __name__ == "__main__":
    main()
